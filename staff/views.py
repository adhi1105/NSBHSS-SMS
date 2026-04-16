import os
import django
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.models import Group, User

# Import Models
from .models import Staff, SubjectAllocation, Department, Subject, LeaveRequest
from admission.models import ClassRoom 
from timetable.models import TimetableEntry 
from student_info.models import Student 
from exam.models import Result 

# Import Forms
from .forms import StaffOnboardingForm, AllocationForm, AssignClassTeacherForm, LeaveRequestForm
from .decorators import is_librarian, is_cashier, is_office_staff, is_dept_admin, is_guest

# --- HELPER FUNCTIONS ---
def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

# NEW HELPER: For modules shared between Admin and Department Head
def is_admin_or_dept_admin(user):
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Dept_Admin']).exists()

def force_custom_role_field(user, role_name):
    """
    Hunts down the custom dropdown field on the User or Profile model 
    and forces it to update, fixing the visual bug in Django Admin.
    """
    if hasattr(user, 'role'):
        user.role = role_name
        user.save(update_fields=['role'])
    elif hasattr(user, 'user_type'):
        user.user_type = role_name
        user.save(update_fields=['user_type'])
    elif hasattr(user, 'profile') and hasattr(user.profile, 'role'):
        user.profile.role = role_name
        user.profile.save(update_fields=['role'])

# NEW: INTELLIGENT ROLE ROUTER
def route_staff_role(staff_profile):
    """
    Reads the staff designation and routes them to the correct non-teaching 
    or teaching security group automatically.
    """
    desig = (staff_profile.designation or "").lower()
    
    if "librarian" in desig:
        target_role = "Librarian"
        is_teaching = False
    elif "cashier" in desig or "accountant" in desig or "finance" in desig:
        target_role = "Cashier"
        is_teaching = False
    elif "office" in desig or "clerk" in desig or "reception" in desig:
        target_role = "Office_Staff"
        is_teaching = False
    elif "admin" in desig or "principal" in desig or "hod" in desig:
        target_role = "Dept_Admin"
        is_teaching = False
    else:
        target_role = "Teacher"
        is_teaching = True

    # 1. Update Staff Profile (This fixes the Telemetry counters!)
    staff_profile.is_teaching_staff = is_teaching
    staff_profile.save(update_fields=['is_teaching_staff'])

    # 2. Update Auth Groups & Permissions
    user = staff_profile.user
    User.objects.filter(id=user.id).update(is_staff=True, is_superuser=False)
    
    group, _ = Group.objects.get_or_create(name=target_role)
    user.groups.clear()
    user.groups.add(group)
    
    # 3. Fix Dropdown View
    force_custom_role_field(user, target_role)
    
    return target_role


# --- 2. STAFF DIRECTORY ---
@login_required
@user_passes_test(is_admin_or_dept_admin)  
def staff_list(request):
    staff_members = Staff.objects.select_related('user', 'department').all().order_by('user__first_name')
    
    # Calculate exact split for Telemetry Cards
    teaching_count = staff_members.filter(is_teaching_staff=True).count()
    non_teaching_count = staff_members.filter(is_teaching_staff=False).count()
    
    return render(request, 'staff/list.html', {
        'staff_members': staff_members,
        'teaching_count': teaching_count,
        'non_teaching_count': non_teaching_count
    })


# --- NEW: NUCLEAR ROLE REPAIR (Fixes the 41 Stuck Teachers) ---
@login_required
@user_passes_test(is_admin) 
def repair_stuck_roles(request):
    """
    Nuclear Fix View: Wipes all groups for the 41 specific usernames
    and forces them into the Teacher group with is_staff enabled using Absolute Override.
    """
    stuck_usernames = [
        'p.j._joseph', 'k.r._gowri', 'sarah_joseph', 'philipose_marar', 'siddharth_pillai', 
        'aswathy_menon', 'k.p._narayanan', 'gopika_parameshwaran', 'asha_gopinath', 'jayan_k', 
        'suresh_pillai', 'latha_mahesh', 'mohandas_nair', 'neethu_s', 'sajith_raghav', 
        'bindu_madhavan', 'reshma_k', 'fathima_beevi', 'rajesh_m', 'lekshmi_nair', 
        'jacob_punnoose', 'kurien_thomas', 'sneha_prakash', 'arjun_das', 'mathew_scaria', 
        'deepa_panicker', 'meera_sankar', 'raji_viswanath', 'suresh_kumarv', 'maya_ramesh', 
        'vishnu_prasad', 'remya_krishnan', 'pradeep_kumar', 'nandini_varma', 'sreedevi_amma', 
        'gautham_krishna', 'saritha_vinod', 'deepak_nair', 'preethi_chandran', 'biju_balakrishnan', 
        'anjali_menon'
    ]

    if request.method == "POST":
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        fixed_count = 0

        with transaction.atomic():
            # Filter users directly to avoid DoesNotExist errors
            users_to_fix = User.objects.filter(username__in=stuck_usernames)
            for user in users_to_fix:
                # 1. Absolute Override: Update DB directly without triggering signals
                User.objects.filter(id=user.id).update(is_staff=True, is_superuser=False)
                # 2. Force Join Table Clear & Add
                user.groups.clear()
                user.groups.add(teacher_group)
                fixed_count += 1

        messages.success(request, f"🚀 Nuclear Fix Complete: {fixed_count} staff members were forcefully synced to the Teacher role.")
        return redirect('staff:staff_list')
    
    return render(request, 'staff/repair_confirm.html', {'stuck_count': len(stuck_usernames)})


# --- WEB-APP ROLE MANAGEMENT (Handles Single & Bulk) ---
@login_required
@user_passes_test(is_admin) 
def sync_staff_roles(request, staff_id):
    student_group = Group.objects.filter(name='Student').first()

    with transaction.atomic():
        if staff_id == 0 and "bulk_promote" in request.POST:
            # UPDATED: We use Staff.objects to get designations for the Router
            all_staff = Staff.objects.select_related('user').all()
            count = 0
            for staff in all_staff:
                # Automatically map to Teacher, Cashier, Librarian, etc.
                route_staff_role(staff)
                count += 1
            messages.success(request, f"Successfully mapped and fixed {count} staff roles based on designation.")

        else:
            staff = get_object_or_404(Staff, id=staff_id)
            user = staff.user
            
            # --- NEW: EXPLICIT ADMIN ELEVATION OVERRIDE ---
            if "make_dept_admin" in request.POST:
                dept_admin_group, _ = Group.objects.get_or_create(name='Dept_Admin')
                user.groups.clear()
                user.groups.add(dept_admin_group)
                force_custom_role_field(user, 'Dept_Admin')
                messages.success(request, f"🌟 {user.get_full_name()} elevated to Department Admin.")

            elif "revoke_dept_admin" in request.POST:
                # Re-run the router to put them back to Teacher/Librarian automatically
                assigned_role = route_staff_role(staff)
                messages.warning(request, f"📉 Admin rights revoked. {user.get_full_name()} reverted to {assigned_role}.")
            # ----------------------------------------------

            elif "promote" in request.POST:
                assigned_role = route_staff_role(staff)
                messages.success(request, f"✅ {user.get_full_name()} mapped to {assigned_role}.")
            
            elif "demote" in request.POST:
                User.objects.filter(id=user.id).update(is_staff=False)
                user.groups.clear()
                if student_group:
                    user.groups.add(student_group)
                
                # THE FIX: Force the custom dropdown field back to Student
                force_custom_role_field(user, 'Student')
                
                messages.warning(request, f"⚠️ {user.get_full_name()} set back to Student.")
        
    return redirect('staff:staff_list')


# --- STAFF PROFILE (Admin View) ---
@login_required
@user_passes_test(is_admin_or_dept_admin) 
def staff_detail(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    subjects = SubjectAllocation.objects.filter(staff=staff).select_related('subject', 'classroom')
    managed_classes = ClassRoom.objects.filter(class_teacher=staff)
    
    return render(request, 'staff/profile_detail.html', {
        'staff': staff,
        'subjects': subjects,
        'managed_classes': managed_classes
    })


# --- 3. ONBOARDING (Admin Only) ---
@login_required
@user_passes_test(is_admin) 
def add_staff(request):
    if request.method == 'POST':
        form = StaffOnboardingForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                staff = form.save()
                
                # UPDATED: Route the newly created staff member dynamically
                assigned_role = route_staff_role(staff)
                
            messages.success(request, f"Onboarded {staff.user.get_full_name()} successfully as {assigned_role}!")
            return redirect('staff:staff_list')
    else:
        form = StaffOnboardingForm()
    
    return render(request, 'staff/add.html', {'form': form})


# --- 4. SUBJECT ALLOCATION (Admin Only) ---
@login_required
@user_passes_test(is_admin_or_dept_admin) 
def allocate_subject(request):
    allocations = SubjectAllocation.objects.select_related('staff', 'subject', 'classroom').order_by('classroom__name')
    
    if request.method == 'POST':
        form = AllocationForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            exists = SubjectAllocation.objects.filter(
                subject=cleaned['subject'], 
                classroom=cleaned['classroom']
            ).exists()
            
            if exists:
                messages.error(request, f"Error: {cleaned['subject']} is already assigned in {cleaned['classroom']}.")
            else:
                form.save()
                messages.success(request, f"Successfully assigned {cleaned['staff']} to {cleaned['subject']}")
                return redirect('staff:allocation_list') 
    else:
        form = AllocationForm()

    form.fields['classroom'].queryset = ClassRoom.objects.all().order_by('standard', 'division')

    return render(request, 'staff/allocation.html', {
        'form': form, 
        'allocations': allocations
    })


# --- 5. WORKLOAD ANALYTICS (Admin Only) ---
@login_required
@user_passes_test(is_admin_or_dept_admin) 
def workload_dashboard(request):
    teacher_workload = Staff.objects.filter(is_teaching_staff=True).annotate(
        subject_count=Count('allocations')
    ).order_by('-subject_count')
    
    return render(request, 'workload/dashboard.html', {'teachers': teacher_workload})

@login_required
@user_passes_test(is_admin_or_dept_admin) 
def delete_allocation(request, allocation_id):
    try:
        allocation = SubjectAllocation.objects.get(id=allocation_id)
        allocation.delete()
        messages.success(request, "Subject allocation removed successfully.")
    except SubjectAllocation.DoesNotExist:
        messages.warning(request, "This item has already been deleted.")
    
    return redirect('staff:allocation_list')


# --- 6. ASSIGN CLASS TEACHER ---
@login_required
@user_passes_test(is_admin) 
def assign_class_teacher(request):
    if request.method == 'POST':
        form = AssignClassTeacherForm(request.POST)
        if form.is_valid():
            target_classroom = form.cleaned_data['classroom']
            new_teacher = form.cleaned_data['staff']
            
            if hasattr(new_teacher, 'class_teacher_of') and new_teacher.class_teacher_of != target_classroom:
                current_class = new_teacher.class_teacher_of
                messages.error(request, f"Error: {new_teacher.user.get_full_name()} is already the Class Teacher of {current_class.name}.")
                return redirect('staff:assign_class_teacher')

            target_classroom.class_teacher = new_teacher
            target_classroom.save()
            
            messages.success(request, f"Success: {new_teacher.user.get_full_name()} assigned to {target_classroom.name}.")
            return redirect('staff:assign_class_teacher')
    else:
        form = AssignClassTeacherForm()

    classrooms = ClassRoom.objects.all().select_related('class_teacher__user').order_by('standard', 'division')
    
    return render(request, 'staff/assign_teacher.html', {
        'form': form,
        'classrooms': classrooms
    })


# --- 6B. AUTO-ASSIGN CLASS TEACHERS ---
@login_required
@user_passes_test(is_admin) 
def auto_assign_class_teachers(request):
    """
    Automatically assigns class teachers based on two rules:
    1. The teacher must teach a core subject in THAT specific classroom.
    2. The teacher must not already be a class teacher for another room.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Fetch all classrooms currently missing a class teacher
                classrooms = ClassRoom.objects.filter(class_teacher__isnull=True).order_by('standard', 'division')
                assigned_count = 0

                for classroom in classrooms:
                    # Query allocations exclusively for this room, excluding those already assigned as class teachers
                    # Exclude non-core/support subjects
                    eligible_allocations = SubjectAllocation.objects.filter(
                        classroom=classroom,
                        staff__class_teacher_of__isnull=True  
                    ).exclude(
                        subject__name__icontains='Physical Education'
                    ).exclude(
                        subject__name__icontains='General'
                    ).select_related('staff')

                    first_eligible = eligible_allocations.first()
                    
                    if first_eligible:
                        classroom.class_teacher = first_eligible.staff
                        classroom.save()
                        assigned_count += 1
                
                if assigned_count > 0:
                    messages.success(request, f"✨ Success! Automatically assigned {assigned_count} class teachers based on their teaching schedules.")
                else:
                    messages.info(request, "No new class teachers were assigned. Classes either already have teachers, or no eligible teachers were found in those classrooms.")
                    
        except Exception as e:
            messages.error(request, f"❌ Error during auto-assignment: {str(e)}")

    return redirect('staff:assign_class_teacher')


# --- 7. REMOVE CLASS TEACHER ---
@login_required
@user_passes_test(is_admin) 
def remove_class_teacher(request, class_id):
    classroom = get_object_or_404(ClassRoom, id=class_id)
    if classroom.class_teacher:
        name = classroom.class_teacher.user.get_full_name()
        classroom.class_teacher = None
        classroom.save()
        messages.warning(request, f"Removed {name} from {classroom.name}.")
    return redirect('staff:assign_class_teacher')


# --- 8. TEACHER PORTAL WITH AUTO-FIX ---
@login_required
def teacher_portal(request):
    try:
        staff_profile = request.user.staff
    except Staff.DoesNotExist:
        default_dept, _ = Department.objects.get_or_create(name="General")
        staff_profile = Staff.objects.create(
            user=request.user,
            department=default_dept,
            designation="Teacher",
            status="active",
            is_teaching_staff=True,
            employee_id=f"TCH-{request.user.id}"
        )
    
    my_allocations = SubjectAllocation.objects.filter(staff=staff_profile).select_related('subject', 'classroom')
    
    return render(request, 'dashboard_teacher.html', {
        'staff': staff_profile,
        'allocations': my_allocations
    })


# --- 9. TEACHER TIMETABLE / WORKLOAD VIEW ---
@login_required
def teacher_timetable(request):
    try:
        staff = request.user.staff
    except Staff.DoesNotExist:
        messages.error(request, "Staff profile missing. Please access the Dashboard first.")
        return redirect('staff:teacher_portal')

    # Fetch what they are SUPPOSED to teach
    allocations = SubjectAllocation.objects.filter(staff=staff).select_related('classroom', 'subject').order_by('classroom__standard', 'classroom__division')

    # Fetch what is ACTUALLY scheduled in the Master Timetable
    actual_counts = TimetableEntry.objects.filter(staff=staff).values('classroom_id', 'subject_id').annotate(period_count=Count('id'))
    
    # Build a fast lookup dictionary: (classroom_id, subject_id) -> total_periods
    count_dict = {(item['classroom_id'], item['subject_id']): item['period_count'] for item in actual_counts}
    
    total_periods_week = 0
    for alloc in allocations:
        # Dynamically attach the actual period count to the allocation object
        alloc.actual_periods = count_dict.get((alloc.classroom_id, alloc.subject_id), 0)
        total_periods_week += alloc.actual_periods

    return render(request, 'staff/timetable.html', {
        'staff': staff,
        'allocations': allocations,
        'total_classes': allocations.count(),
        'total_periods_week': total_periods_week # Pass the grand total to the template
    })


# --- 10. AUTO-WORKLOAD MAINTENANCE ---
@login_required
@user_passes_test(is_admin_or_dept_admin) 
def auto_distribute_workload(request):
    STREAM_MAP = {
        "Biology Science": ["Physics", "Chemistry", "Biology", "English", "Malayalam", "Hindi", "Arabic", "Mathematics"],
        "Home Science": ["Physics", "Chemistry", "Biology", "English", "Malayalam", "Hindi", "Arabic", "Home Science"],
        "Computer Science": ["Physics", "Chemistry", "English", "Malayalam", "Hindi", "Arabic", "Computer Science", "Computer Application", "Mathematics"],
        "Commerce": ["Accountancy", "Business Studies", "Economics", "English", "Malayalam", "Hindi", "Arabic"],
        "Humanities": ["History", "Economics", "Political Science", "Sociology", "English", "Malayalam", "Hindi", "Arabic"]
    }

    try:
        with transaction.atomic():
            SubjectAllocation.objects.all().delete()
            all_staff = list(Staff.objects.all().exclude(designation__icontains="Physical Education"))
            total_teachers = len(all_staff)
            
            if total_teachers == 0:
                messages.error(request, "❌ No teachers found! Please add staff first.")
                return redirect('staff:workload')

            calculated_limit = max(4, int(150 / total_teachers) + 1)

            subject_pools = {}
            for teacher in all_staff:
                desig = (teacher.designation or "").lower()
                assigned_sub = None
                
                if "hindi" in desig: assigned_sub = "Hindi"
                elif "arabic" in desig: assigned_sub = "Arabic"
                elif "computer application" in desig: assigned_sub = "Computer Application"
                elif "geography" in desig: assigned_sub = "Geography"
                else:
                    all_subs = set([s for sublist in STREAM_MAP.values() for s in sublist])
                    for s in all_subs:
                        if s.lower() in desig:
                            assigned_sub = s
                            break
                
                if not assigned_sub:
                    assigned_sub = "General"

                if assigned_sub not in subject_pools:
                    subject_pools[assigned_sub] = []
                subject_pools[assigned_sub].append({'staff': teacher, 'load': 0})

            classrooms = ClassRoom.objects.select_related('stream').all().order_by('standard', 'division')

            for classroom in classrooms:
                stream_name = classroom.stream.name if classroom.stream else None
                required_subjects = STREAM_MAP.get(stream_name, [])

                for sub_name in required_subjects:
                    pool = subject_pools.get(sub_name, [])
                    assigned_teacher = None
                    
                    if pool:
                        pool.sort(key=lambda x: x['load'])
                        for expert_info in pool:
                            if expert_info['load'] < calculated_limit: 
                                assigned_teacher = expert_info['staff']
                                expert_info['load'] += 1
                                break
                    
                    if not assigned_teacher and "General" in subject_pools:
                        gen_pool = subject_pools["General"]
                        gen_pool.sort(key=lambda x: x['load'])
                        for g_info in gen_pool:
                            if g_info['load'] < calculated_limit:
                                assigned_teacher = g_info['staff']
                                g_info['load'] += 1
                                break

                    if assigned_teacher:
                        subject_obj, _ = Subject.objects.get_or_create(name=sub_name)
                        SubjectAllocation.objects.create(
                            staff=assigned_teacher,
                            subject=subject_obj,
                            classroom=classroom
                        )

        messages.success(request, f"✅ Balanced Distribution! {total_teachers} teachers assigned approx {calculated_limit} classes each.")
    
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")

    return redirect('staff:workload')


# --- 11. AUTOMATIC PROMOTION ENGINE (Grade 11 -> Grade 12) ---
@login_required
@user_passes_test(is_admin_or_dept_admin)
def promotion_terminal(request):
    """
    Final Exam Promotion Node: Migrates eligible Grade 11 students to Grade 12 
    based on passing criteria in the Result registry.
    """
    if request.method == 'POST':
        source_id = request.POST.get('source_class')
        target_id = request.POST.get('target_class')
        pass_mark = int(request.POST.get('pass_mark', 35))

        source_class = get_object_or_404(ClassRoom, id=source_id)
        target_class = get_object_or_404(ClassRoom, id=target_id)
        
        eligible_students = Student.objects.filter(classroom=source_class, is_active=True)
        promoted_count = 0
        failed_count = 0

        with transaction.atomic():
            for student in eligible_students:
                # Check for failing grades in any core subject in the Final exam
                has_failed = Result.objects.filter(
                    student=student, 
                    marks_obtained__lt=pass_mark,
                    exam__exam_type='FINAL'
                ).exists()

                if not has_failed:
                    # Migrate to target class
                    student.classroom = target_class
                    student.save()
                    promoted_count += 1
                else:
                    failed_count += 1
        
        messages.success(request, f"Migration Terminal Complete: {promoted_count} Promoted, {failed_count} Retained.")
        return redirect('staff:staff_list')

    classrooms_11 = ClassRoom.objects.filter(standard='11')
    classrooms_12 = ClassRoom.objects.filter(standard='12')
    
    return render(request, 'staff/promotion_terminal.html', {
        'classrooms_11': classrooms_11,
        'classrooms_12': classrooms_12
    })


# --- DASHBOARDS ---
@login_required
@user_passes_test(is_librarian)
def librarian_dashboard(request):
    # Logic to fetch library stats (Total books, Issued, Overdue)
    return render(request, 'dashboards/librarian.html')

@login_required
@user_passes_test(is_cashier)
def cashier_dashboard(request):
    # Logic to fetch fee collections, pending dues, invoices
    return render(request, 'dashboards/cashier.html')

@login_required
@user_passes_test(is_office_staff)
def office_staff_dashboard(request):
    # Logic for admission stats, user role management requests
    return render(request, 'dashboards/office_staff.html')

@login_required
@user_passes_test(is_dept_admin)
def dept_admin_dashboard(request):
    # Logic for attendance correction, mark edits, staff overview
    return render(request, 'dashboards/dept_admin.html')

@user_passes_test(is_guest)
def guest_dashboard(request):
    # Public-facing or basic logged-in view for admission tracking
    return render(request, 'dashboards/guest_admission.html')

# --- 12. LEAVE REQUEST PORTAL ---
@login_required
def leave_request_portal(request):
    try:
        staff_profile = request.user.staff
    except Staff.DoesNotExist:
        messages.error(request, "Staff profile is missing. Please contact Administration.")
        return redirect('home')

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_req = form.save(commit=False)
            leave_req.staff = staff_profile
            leave_req.save()
            messages.success(request, "Leave request submitted successfully. Awaiting approval.")
            return redirect('staff:leave_request_portal')
    else:
        form = LeaveRequestForm()

    # Get their past leave requests
    history = LeaveRequest.objects.filter(staff=staff_profile).order_by('-applied_on')
    
    # Calculate some basic stats
    approved_leaves = history.filter(status='Approved').count()
    pending_leaves = history.filter(status='Pending').count()

    return render(request, 'staff/leave_request.html', {
        'form': form,
        'history': history,
        'staff_profile': staff_profile,
        'approved_leaves': approved_leaves,
        'pending_leaves': pending_leaves
    })