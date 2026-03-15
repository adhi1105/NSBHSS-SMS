import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Count

from admission.models import ClassRoom
from staff.models import Staff, SubjectAllocation 
from school_system.models import Subject
from student_info.models import Student
from .models import TimetableEntry, TimeSlot

# --- Stream Specialization Mapping (Refined) ---
# Malayalam and Hindi merged; Arabic and Computer Applications removed.
# This mapping ensures only stream-specific subjects appear in the selector.
STREAM_SUBJECT_MAPPING = {
    'Home Science': ['Physics', 'Chemistry', 'Biology', 'English', 'Malayalam/Hindi', 'Home Science'],
    'Biology Science': ['Physics', 'Chemistry', 'Biology', 'English', 'Malayalam/Hindi', 'Mathematics'],
    'Computer Science': ['Physics', 'Chemistry', 'English', 'Malayalam/Hindi', 'Computer Science', 'Mathematics'],
    'Commerce': ['Accountancy', 'Business Studies', 'Economics', 'English', 'Malayalam/Hindi'],
    'Humanities': ['History', 'Economics', 'Political Science', 'Sociology', 'English', 'Malayalam/Hindi']
}

# --- Security Helpers ---

def is_admin(user):
    """Check if the user has full administrative rights."""
    return user.is_superuser or user.groups.filter(name='Admin').exists()

def is_staff(user):
    """Check if the user is an Admin or a Teacher (linked to a Staff profile)."""
    return is_admin(user) or hasattr(user, 'staff') or user.groups.filter(name='Teacher').exists()

def get_teacher_allowed_classes(user):
    """Returns ClassRooms assigned to the teacher via SubjectAllocation."""
    if is_admin(user):
        return ClassRoom.objects.filter(standard__in=[11, 12])
    
    try:
        staff_profile = user.staff
        assigned_ids = SubjectAllocation.objects.filter(staff=staff_profile).values_list('classroom_id', flat=True)
        return ClassRoom.objects.filter(id__in=assigned_ids, standard__in=[11, 12]).distinct()
    except AttributeError:
        assigned_ids = SubjectAllocation.objects.filter(staff__user=user).values_list('classroom_id', flat=True)
        return ClassRoom.objects.filter(id__in=assigned_ids, standard__in=[11, 12]).distinct()

# --- 1. TRAFFIC CONTROLLER ---

@login_required
def index(request):
    """ Routes user based on role to their respective landing pages. """
    if is_staff(request.user):
        return redirect('timetable:manage_timetable') 

    try:
        student = Student.objects.select_related('classroom').get(user=request.user)
        return redirect('timetable:view_timetable', classroom_id=student.classroom.id)
    except (AttributeError, Student.DoesNotExist):
        messages.error(request, "Student Profile Not Found.")
        return render(request, 'error.html', {'message': "Profile Not Found."})

# --- NEW: CLASS TEACHER TIMETABLE EDITOR ---

@login_required
def manage_class_timetable(request):
    """ Protected view allowing Class Teachers to edit their specific classroom's timetable. """
    try:
        teacher = request.user.staff
        # 1. SECURITY CHECK: Ensure they are actually a class teacher
        classroom = teacher.class_teacher_of
        if not classroom:
            messages.error(request, "Access Denied: You are not assigned as a Class Teacher.")
            return redirect('staff:teacher_portal')
    except AttributeError:
        return redirect('staff:teacher_portal')

    # 2. Fetch all teachers allocated to teach this specific class
    available_allocations = SubjectAllocation.objects.filter(classroom=classroom).select_related('staff', 'subject')

    # 3. Handle Form Submission (Adding/Deleting a period)
    if request.method == 'POST':
        if 'add_period' in request.POST:
            day = request.POST.get('day')
            period_num = request.POST.get('period')
            allocation_id = request.POST.get('allocation')
            
            if day and period_num and allocation_id:
                allocation = get_object_or_404(SubjectAllocation, id=allocation_id, classroom=classroom)
                
                # Fetch the TimeSlot object based on period number (1 to 8/9)
                try:
                    # Assuming periods are ordered chronologically, excluding breaks
                    academic_slots = list(TimeSlot.objects.filter(is_break=False).order_by('start_time'))
                    target_slot = academic_slots[int(period_num) - 1]
                except (IndexError, ValueError):
                    messages.error(request, "Invalid period number selected.")
                    return redirect('timetable:manage_class')

                # Conflict Check: Is the teacher busy elsewhere at this exact time?
                conflict = TimetableEntry.objects.filter(
                    day=day, 
                    time_slot=target_slot, 
                    staff=allocation.staff
                ).exclude(classroom=classroom).exists()
                
                if conflict:
                    messages.error(request, f"Conflict: {allocation.staff.user.get_full_name()} is already teaching another class during Period {period_num} on {day}.")
                else:
                    TimetableEntry.objects.update_or_create(
                        classroom=classroom,
                        day=day,
                        time_slot=target_slot,
                        defaults={
                            'subject': allocation.subject,
                            'staff': allocation.staff
                        }
                    )
                    messages.success(request, f"Period {period_num} on {day} updated successfully.")
            
        elif 'delete_period' in request.POST:
            slot_id = request.POST.get('slot_id')
            TimetableEntry.objects.filter(id=slot_id, classroom=classroom).delete()
            messages.warning(request, "Timetable slot cleared.")
            
        return redirect('timetable:manage_class')

    # 4. Fetch Current Schedule for the grid
    raw_schedule = TimetableEntry.objects.filter(classroom=classroom).select_related('subject', 'staff__user', 'time_slot').order_by('time_slot__start_time')
    
    # Map academic slots to integer periods (1, 2, 3...)
    academic_slots = list(TimeSlot.objects.filter(is_break=False).order_by('start_time'))
    slot_to_period = {slot.id: str(idx + 1) for idx, slot in enumerate(academic_slots)}

    schedule = {day: {} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']}
    for entry in raw_schedule:
        if entry.time_slot_id in slot_to_period:
            period_str = slot_to_period[entry.time_slot_id]
            schedule[entry.day][period_str] = entry

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = list(range(1, len(academic_slots) + 1)) 

    return render(request, 'timetable/manage_class.html', {
        'classroom': classroom,
        'schedule': schedule,
        'allocations': available_allocations,
        'days': days,
        'periods': periods
    })

# --- 2. GRID VIEW & BULK SAVE (Optimized for 3-2-2-2 & Monday-Friday) ---

@login_required
def view_timetable(request, classroom_id):
    """ Renders the interactive grid and handles bulk JSON schedule updates for a 5-day week. """
    classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    stream_name = classroom.stream.name
    
    # Permission Check for Teachers
    if is_staff(request.user) and not is_admin(request.user):
        allowed_classes = get_teacher_allowed_classes(request.user)
        if classroom not in allowed_classes:
            messages.error(request, "Access Denied.")
            return redirect('timetable:manage_timetable')
            
    # Period Numbering logic: Critical to order by start_time for 3-2-2-2 order chronology
    raw_slots = TimeSlot.objects.all().order_by('start_time')
    time_slots = []
    academic_count = 1
    for slot in raw_slots:
        if slot.is_break:
            # Detect break type based on 12:45 lunch schedule
            start_str = slot.start_time.strftime('%H:%M')
            if start_str == "12:45":
                slot.display_label = "LUNCH"
            else:
                slot.display_label = "REST" 
        else:
            slot.display_label = f"P{academic_count}"
            academic_count += 1
        time_slots.append(slot)

    # Updated for a 5-day school week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # POST handling for Bulk Sync from the Frontend Grid
    if request.method == "POST":
        if not is_admin(request.user):
            return JsonResponse({'status': 'error', 'message': 'Permission Denied.'}, status=403)
            
        try:
            data = json.loads(request.body)
            new_schedule = data.get('schedule', [])
            allowed_names = STREAM_SUBJECT_MAPPING.get(stream_name, [])

            with transaction.atomic():
                # Wipe current class entries but exclude Saturday if any exist
                TimetableEntry.objects.filter(classroom=classroom).delete()
                for item in new_schedule:
                    day = item['day']; slot_id = item['slot_id']; subject_id = item['subject_id']
                    
                    if day == 'Saturday': continue # Safety exclusion

                    try:
                        alloc = SubjectAllocation.objects.get(classroom=classroom, subject_id=subject_id)
                        if alloc.subject.name not in allowed_names:
                            continue # Skip non-stream subjects
                        
                        teacher = alloc.staff
                        # Global conflict check for the teacher across all classrooms
                        if TimetableEntry.objects.filter(staff=teacher, day=day, time_slot_id=slot_id).exists():
                            return JsonResponse({'status': 'error', 'message': f'Conflict for {teacher.user.get_full_name()} on {day}'}, status=400)

                        TimetableEntry.objects.create(classroom=classroom, subject_id=subject_id, staff=teacher, day=day, time_slot_id=slot_id)
                    except SubjectAllocation.DoesNotExist:
                        return JsonResponse({'status': 'error', 'message': 'Teacher Allocation Missing.'}, status=400)
            
            return JsonResponse({'status': 'success', 'message': 'Timetable synced successfully!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # Filtering subjects based on stream specialization
    allowed_names = STREAM_SUBJECT_MAPPING.get(stream_name, [])
    
    # Show entries already in the timetable
    entries = TimetableEntry.objects.filter(classroom=classroom, subject__name__in=allowed_names).select_related('subject', 'staff__user', 'time_slot')
    
    timetable_data = {day: {} for day in days}
    for entry in entries:
        if entry.day in timetable_data: # Exclude Saturday from rendering
            timetable_data[entry.day][entry.time_slot.id] = entry

    # Context subjects list: show stream-appropriate subjects that have an allocation
    allocated_subjects = Subject.objects.filter(
        id__in=SubjectAllocation.objects.filter(classroom=classroom).values_list('subject_id', flat=True),
        name__in=allowed_names
    ).distinct()

    context = {
        'classroom': classroom, 'time_slots': time_slots, 'days': days,
        'timetable_data': timetable_data, 'subjects': allocated_subjects,
        'is_staff_user': is_staff(request.user), 'can_edit': is_admin(request.user) 
    }
    return render(request, 'timetable/detail.html', context)

# --- 3. MANAGE LIST ---

@login_required
def manage_timetable(request):
    """ Displays the master list of classrooms for management. """
    if not is_staff(request.user):
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    classrooms = get_teacher_allowed_classes(request.user).order_by('standard', 'division', 'stream')
    return render(request, 'timetable/manage_list.html', {
        'classrooms': classrooms,
        'is_restricted': not is_admin(request.user)
    })

# --- 4. WORKLOAD & ARRANGEMENT ---

@login_required
def teacher_workload_analysis(request):
    """ View to analyze teacher workload for arrangement optimization and substitution. """
    if not is_admin(request.user):
        return redirect('home')

    # Calculate total academic periods per week for each teacher across all classrooms
    workload_data = Staff.objects.annotate(
        periods_per_week=Count('timetableentry')
    ).order_by('periods_per_week')

    return render(request, 'timetable/workload_analysis.html', {
        'workload_data': workload_data
    })

# --- 5. INDIVIDUAL ADD (Admin Only) ---

@login_required
def add_entry(request, class_id, day, slot_id):
    """ Manual modal-based entry addition for precise scheduling. """
    if not is_admin(request.user):
        return redirect('timetable:manage_timetable')

    classroom = get_object_or_404(ClassRoom, pk=class_id)
    stream_name = classroom.stream.name
    slot = get_object_or_404(TimeSlot, pk=slot_id)
    allowed_names = STREAM_SUBJECT_MAPPING.get(stream_name, [])
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        try:
            allocation = SubjectAllocation.objects.get(classroom=classroom, subject_id=subject_id)
            if allocation.subject.name not in allowed_names:
                messages.error(request, "Subject not allowed for this stream.")
            else:
                teacher = allocation.staff
                # Strict check for double-booking of teachers across the school
                if TimetableEntry.objects.filter(staff=teacher, day=day, time_slot=slot).exclude(classroom=classroom).exists():
                    messages.error(request, "Teacher double-booking detected in another classroom.")
                else:
                    TimetableEntry.objects.update_or_create(classroom=classroom, day=day, time_slot=slot, defaults={'subject_id': subject_id, 'staff': teacher})
                    messages.success(request, f"Schedule updated for {day} {slot.start_time}.")
        except SubjectAllocation.DoesNotExist:
            messages.error(request, "Teacher allocation missing for this subject.")
        return redirect('timetable:view_timetable', classroom_id=class_id)

    subjects = Subject.objects.filter(
        id__in=SubjectAllocation.objects.filter(classroom=classroom).values_list('subject_id', flat=True),
        name__in=allowed_names
    )
    return render(request, 'timetable/add_modal.html', {'classroom': classroom, 'day': day, 'slot': slot, 'subjects': subjects})

# --- 6. DELETE SLOT (Admin Only) ---

@login_required
def delete_entry(request, entry_id):
    """ Deletes a specific academic entry from the grid. """
    if not is_admin(request.user):
        return redirect('timetable:manage_timetable')
    entry = get_object_or_404(TimetableEntry, id=entry_id)
    cid = entry.classroom.id
    entry.delete()
    return redirect('timetable:view_timetable', classroom_id=cid)

# --- 7. AJAX CONFLICT CHECKERS ---

def check_teacher_conflict(request):
    """ Real-time validation for form-based entry to prevent human error. """
    try:
        allocation = SubjectAllocation.objects.get(classroom_id=request.GET.get('classroom_id'), subject_id=request.GET.get('subject_id'))
        teacher = allocation.staff
        conflict = TimetableEntry.objects.filter(staff=teacher, day=request.GET.get('day'), time_slot_id=request.GET.get('slot_id')).exclude(classroom_id=request.GET.get('classroom_id')).first()
        if conflict:
            return JsonResponse({'conflict': True, 'message': f'{teacher.user.get_full_name()} is busy in {conflict.classroom.name}'})
        return JsonResponse({'conflict': False, 'teacher_name': teacher.user.get_full_name()})
    except Exception:
        return JsonResponse({'conflict': True, 'message': 'Database Retrieval Error.'})
    
def check_drag_conflict(request):
    """ Real-time validation for drag-and-drop feedback on the interactive grid. """
    try:
        allocation = SubjectAllocation.objects.get(classroom_id=request.GET.get('classroom_id'), subject_id=request.GET.get('subject_id'))
        teacher = allocation.staff
        conflict = TimetableEntry.objects.filter(staff=teacher, day=request.GET.get('day'), time_slot_id=request.GET.get('slot_id')).exclude(classroom_id=request.GET.get('classroom_id')).first()
        if conflict:
            return JsonResponse({'status': 'conflict', 'message': f'Busy in {conflict.classroom.name}'})
        return JsonResponse({'status': 'available', 'teacher': teacher.user.first_name})
    except Exception:
        return JsonResponse({'status': 'no_allocation'})

# --- 8. SMART AUTO-FILL (Optimized for 9-Period 5-Day Week with Conflict Retry) ---

@login_required
@user_passes_test(is_admin)
def auto_fill_timetable(request, classroom_id):
    """ Improved Auto-Fill with multi-subject retry logic to ensure zero empty slots where possible. """
    classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    stream_name = classroom.stream.name
    allowed_names = STREAM_SUBJECT_MAPPING.get(stream_name, [])
    
    # Strictly Monday to Friday (5 Days)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    # Fetch academic slots only (9 slots total in 3-2-2-2 order)
    time_slots = TimeSlot.objects.filter(is_break=False).order_by('start_time')

    if request.method == "POST":
        try:
            with transaction.atomic():
                TimetableEntry.objects.filter(classroom=classroom).delete()
                # Get all teacher-subject pairings specifically allocated to this class
                alloc_pool = list(SubjectAllocation.objects.filter(
                    classroom=classroom, subject__name__in=allowed_names
                ).select_related('staff', 'subject'))

                if not alloc_pool:
                    return JsonResponse({'status': 'error', 'message': 'No subject allocations found.'})

                for day in days:
                    for slot in time_slots:
                        # Shuffle subjects for EVERY slot to maximize placement permutations
                        random.shuffle(alloc_pool)
                        
                        placed = False
                        for target in alloc_pool:
                            teacher = target.staff
                            # Conflict Shield: Check if this teacher is currently in another room
                            is_busy = TimetableEntry.objects.filter(
                                staff=teacher, day=day, time_slot=slot
                            ).exists()
                            
                            if not is_busy:
                                TimetableEntry.objects.create(
                                    classroom=classroom, subject=target.subject, 
                                    staff=teacher, day=day, time_slot=slot
                                )
                                placed = True
                                break # Move to the next slot once a free teacher is found
                        
                        # Logic note: If 'placed' is still False here, every teacher allocated 
                        # to this class is busy elsewhere during this specific time slot.
            
            return JsonResponse({'status': 'success', 'message': f'Timetable for {classroom.name} generated!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required
@user_passes_test(is_admin)
def clear_timetable(request, classroom_id):
    """ Wipes all scheduled academic entries for the specific classroom. """
    if request.method == "POST":
        classroom = get_object_or_404(ClassRoom, pk=classroom_id)
        TimetableEntry.objects.filter(classroom=classroom).delete()
        return JsonResponse({'status': 'success', 'message': 'Class grid cleared successfully.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})