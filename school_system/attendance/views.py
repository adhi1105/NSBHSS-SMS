import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Count
from django.forms import modelformset_factory, Select, Textarea

# --- Import Models ---
from .models import AttendanceLog, AttendanceRecord
from student_info.models import Student
from admission.models import ClassRoom
from staff.models import Staff, SubjectAllocation 

# ==========================================
# 0. HELPER: GET TEACHER'S CLASSES
# ==========================================
def get_teacher_assigned_classes(user):
    """
    Returns ClassRooms where the user is either:
    1. The designated 'Class Teacher'
    2. Assigned to teach a subject (SubjectAllocation)
    """
    if user.is_superuser:
        return ClassRoom.objects.all().order_by('standard', 'division')
    
    # Robust check for staff profile
    if hasattr(user, 'staff'):
        staff = user.staff
        
        # 1. Classes where they are the official Class Teacher
        class_teacher_classes = ClassRoom.objects.filter(class_teacher=staff)
        
        # 2. Classes where they teach a subject
        subject_classes = ClassRoom.objects.filter(
            id__in=SubjectAllocation.objects.filter(staff=staff).values_list('classroom_id', flat=True)
        )
        
        # Combine and distinct
        return (class_teacher_classes | subject_classes).distinct().order_by('standard', 'division')
        
    return ClassRoom.objects.none()

# ==========================================
# 1. TRAFFIC CONTROLLER (Index) & STUDENT VIEW
# ==========================================
@login_required
def index(request):
    """ 
    Redirects users based on their role. 
    Added: Advanced filtration (Daily/Date-wise, Monthly, Yearly) for students.
    """
    
    # A. Staff / Admin -> Select Class
    if request.user.is_superuser or hasattr(request.user, 'staff'):
        return redirect('attendance:select_class')
    
    # B. Student -> View Own Stats with Filtration
    try:
        student = Student.objects.get(user=request.user)
        filter_type = request.GET.get('filter', 'daily')
        today = timezone.now().date()
        
        # Base Queryset
        my_records = AttendanceRecord.objects.filter(student=student).select_related(
            'log__subject', 
            'log__taken_by__user'
        ).order_by('-log__date', '-log__timestamp')
        
        # Filtration Logic
        selected_date_str = request.GET.get('date')
        query_date = today

        if filter_type == 'daily':
            if selected_date_str:
                try:
                    query_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                except ValueError:
                    query_date = today
            my_records = my_records.filter(log__date=query_date)
            context_label = query_date.strftime('%d %b, %Y')
            
        elif filter_type == 'monthly':
            month = int(request.GET.get('month', today.month))
            year = int(request.GET.get('year', today.year))
            my_records = my_records.filter(log__date__month=month, log__date__year=year)
            context_label = datetime(year, month, 1).strftime('%B %Y')
            
        elif filter_type == 'yearly':
            year = int(request.GET.get('year', today.year))
            my_records = my_records.filter(log__date__year=year)
            context_label = str(year)

        # Statistics Calculation
        total_slots = my_records.count()
        present_slots = my_records.filter(status='present').count()
        percentage = (present_slots / total_slots * 100) if total_slots > 0 else 0.0

        context = {
            'records': my_records,
            'total_days': total_slots, 
            'present_days': present_slots,
            'percentage': round(percentage, 1),
            'student': student,
            'filter_type': filter_type,
            'context_label': context_label,
            'selected_date': query_date.strftime('%Y-%m-%d'),
            'today': today,
        }
        return render(request, 'attendance/student_index.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Profile not found. Please contact admin.")
        return redirect('home')

# ==========================================
# 2. TEACHER: SELECT CLASS
# ==========================================
@login_required
def select_class(request):
    is_staff = hasattr(request.user, 'staff')
    is_superuser = request.user.is_superuser
    
    if not (is_superuser or is_staff):
        messages.error(request, "Access Denied: You are not registered as a Staff member.")
        return redirect('home')
    
    classes = get_teacher_assigned_classes(request.user)
    
    return render(request, 'attendance/select_class.html', {
        'classes': classes, 
        'my_classes': classes, 
        'is_restricted': not is_superuser 
    })

# ==========================================
# 3. MARK ATTENDANCE (Role-Based Logic)
# ==========================================
@login_required
def mark_attendance(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    today = timezone.now().date()
    
    # A. Access Control
    is_staff_user = hasattr(request.user, 'staff')
    is_superuser = request.user.is_superuser

    if not (is_superuser or is_staff_user):
        messages.error(request, "Access Denied.")
        return redirect('home')
    
    allowed_classes = get_teacher_assigned_classes(request.user)
    if not is_superuser and classroom not in allowed_classes:
        messages.error(request, "Access Denied: You are not assigned to this class.")
        return redirect('attendance:select_class')

    # B. THE "ONE DAY" LOGIC: Class Teacher vs Subject Teacher
    staff = request.user.staff if is_staff_user else None
    is_class_teacher = (classroom.class_teacher == staff)
    
    # If they are the class teacher, we mark "General" attendance (subject=None) 
    # for the entire day. If they are just a subject teacher, we mark per subject.
    subject = None
    if not is_class_teacher and staff:
        allocation = SubjectAllocation.objects.filter(staff=staff, classroom=classroom).first()
        if allocation:
            subject = allocation.subject
    
    # C. Get or Create Log (Unique per Day + Subject + Class)
    log_session, created = AttendanceLog.objects.get_or_create(
        classroom=classroom,
        date=today,
        subject=subject,
        defaults={'taken_by': staff}
    )

    # D. SYNC STUDENTS (Ensure everyone is in the record)
    current_students = Student.objects.filter(classroom=classroom).order_by('roll_number')
    existing_ids = AttendanceRecord.objects.filter(log=log_session).values_list('student_id', flat=True)
    missing_students = current_students.exclude(id__in=existing_ids)

    if missing_students.exists():
        AttendanceRecord.objects.bulk_create([
            AttendanceRecord(log=log_session, student=s, status='present') 
            for s in missing_students
        ])

    # E. PREPARE FORMSET
    AttendanceFormSet = modelformset_factory(
        AttendanceRecord,
        fields=('status', 'remarks'),
        extra=0,
        can_delete=False,
        widgets={
            'status': Select(attrs={'class': 'd-none'}),
            'remarks': Textarea(attrs={'class': 'form-control', 'rows': 1, 'placeholder': 'Optional note...'})
        }
    )

    queryset = AttendanceRecord.objects.filter(log=log_session).select_related('student__user').order_by('student__roll_number')

    # F. Handle Submission (Update or Create logic)
    if request.method == 'POST':
        formset = AttendanceFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            
            display_name = subject.name if subject else "General Attendance"
            messages.success(request, f"✅ {display_name} saved for {classroom.name}")
            return redirect('attendance:select_class')
        else:
            messages.error(request, "Error saving attendance.")
    else:
        formset = AttendanceFormSet(queryset=queryset)

    return render(request, 'attendance/mark.html', {
        'formset': formset,   
        'classroom': classroom,
        'date': today, 
        'log': log_session,
        'subject': subject,
        'is_class_teacher': is_class_teacher
    })

# ==========================================
# 4. VIEW HISTORY
# ==========================================
@login_required
def view_history(request, classroom_id):
    if not (request.user.is_superuser or hasattr(request.user, 'staff')):
        return redirect('home')

    selected_date = request.GET.get('date')
    if selected_date:
        return redirect('attendance:date_report', classroom_id=classroom_id, date=selected_date)

    classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    logs = AttendanceLog.objects.filter(classroom=classroom).order_by('-date', '-timestamp')

    context = {
        'classroom': classroom,
        'logs': logs,
    }
    return render(request, 'attendance/history.html', context)

# ==========================================
# 5. VIEW DATE REPORT
# ==========================================
@login_required
def view_date_report(request, classroom_id, date):
    if not (request.user.is_superuser or hasattr(request.user, 'staff')):
        return redirect('home')

    classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    
    try:
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Invalid Date Format")
        return redirect('attendance:history', classroom_id=classroom.id)

    logs = AttendanceLog.objects.filter(classroom=classroom, date=report_date).select_related('subject', 'taken_by__user')
    log = logs.first()
    
    if log:
        records = AttendanceRecord.objects.filter(log=log).select_related('student__user').order_by('student__roll_number')
        present_count = records.filter(status='present').count()
        absent_count = records.filter(status='absent').count()
        late_count = records.filter(status='late').count()
        taken_by = log.taken_by
    else:
        records = []
        present_count = 0; absent_count = 0; late_count = 0
        taken_by = None

    context = {
        'classroom': classroom,
        'report_date': report_date,
        'log': log,
        'logs': logs,
        'taken_by': taken_by,
        'records': records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
    }
    return render(request, 'attendance/date_report.html', context)