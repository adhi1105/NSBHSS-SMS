from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from .models import Exam, Result
from admission.models import ClassRoom
from school_system.models import Subject
from student_info.models import Student
from .forms import ExamForm
from staff.models import Staff, SubjectAllocation

# --- HELPER: Calculate Grade (Kerala HSE Standard: 30 is Pass) ---
def calculate_grade(mark):
    """
    Standard Kerala Grading:
    A+: 90-100, A: 80-89, B+: 70-79, B: 60-69, C+: 50-59, C: 40-49, D+: 30-39, E: <30
    """
    if mark is None or mark == "":
        return "-"
    try:
        m = float(mark)
        if m >= 90: return "A+"
        elif m >= 80: return "A"
        elif m >= 70: return "B+"
        elif m >= 60: return "B"
        elif m >= 50: return "C+"
        elif m >= 40: return "C"
        elif m >= 30: return "D+"  
        else: return "E"           
    except (ValueError, TypeError):
        return "-"

# --- ROLE CHECKS ---
def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

def is_admin_or_dept_admin(user):
    """ NEW: Grants oversight permissions to Department Heads as well as Admins """
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Dept_Admin']).exists()

def is_teacher(user):
    """ Teachers have access to the entry portal, as do Dept Admins and Root Admins """
    return user.groups.filter(name='Teacher').exists() or is_admin_or_dept_admin(user)

# --- 1. TRAFFIC CONTROLLER ---
@login_required
def entry_index(request):
    """ Routes users based on identity: Admin/Dept Head -> Dashboard, Teacher -> Selection, Student -> Results """
    if is_admin_or_dept_admin(request.user): # <--- UPDATED CLEARANCE
        return redirect('exam:admin_dashboard')
    elif is_teacher(request.user):
        return redirect('exam:teacher_select')
    else:
        # STUDENT VIEW: Aggregate results into reports
        try:
            student = Student.objects.get(user=request.user)
            # Students only see published exams
            exams = Exam.objects.filter(is_published=True).order_by('-start_date')
            reports = []
            
            for exam in exams:
                results_qs = Result.objects.filter(student=student, exam=exam).select_related('subject')
                
                if results_qs.exists():
                    total_obt = results_qs.aggregate(Sum('marks_obtained'))['marks_obtained__sum'] or 0
                    # Note: We assume Result model has a 'total_marks' field; otherwise use exam.total_marks
                    total_max = results_qs.aggregate(Sum('total_marks'))['total_marks__sum'] or 0
                    percent = (total_obt / total_max * 100) if total_max > 0 else 0.0
                    
                    # Attach grades to individual results for the template
                    for r in results_qs:
                        r.grade = calculate_grade(r.marks_obtained)

                    reports.append({
                        'exam': exam,
                        'results': results_qs,
                        'total_obt': round(total_obt, 2),
                        'percent': round(percent, 2),
                        'status': "PASSED" if percent >= 30 else "FAILED"
                    })

            return render(request, 'exam/student_index.html', {'student': student, 'reports': reports})
            
        except Student.DoesNotExist:
            return render(request, 'error.html', {'message': "No Student Profile linked to this user."})

# --- 2. ADMIN DASHBOARD ---
@login_required
@user_passes_test(is_admin_or_dept_admin) # <--- UPDATED CLEARANCE
def admin_dashboard(request):
    """ Management view for administrators to see all exams """
    exams = Exam.objects.all().order_by('-start_date')
    return render(request, 'exam/admin_index.html', {'exams': exams})

# --- 3. TEACHER SELECTION ---
@login_required
@user_passes_test(is_teacher)
def teacher_select(request):
    """ Filters classes and subjects based on teacher workload allocations """
    user = request.user
    
    if is_admin_or_dept_admin(user): # <--- UPDATED CLEARANCE: Dept Heads see all classes
        classes = ClassRoom.objects.all().order_by('standard', 'division')
        exams = Exam.objects.filter(is_active=True, is_locked=False)
    else:
        # Get only classrooms where this specific teacher has a SubjectAllocation
        my_allocations = SubjectAllocation.objects.filter(staff__user=user)
        classes = ClassRoom.objects.filter(
            id__in=my_allocations.values_list('classroom_id', flat=True)
        ).distinct().order_by('standard', 'division')
        
        # Only show active/unlocked exams for entry
        exams = Exam.objects.filter(is_active=True, is_locked=False)

    selected_class_id = request.GET.get('classroom')
    subjects = Subject.objects.none()

    if selected_class_id:
        selected_class = get_object_or_404(ClassRoom, id=selected_class_id)
        
        # Security Enforcement: Ensure teacher actually teaches in this class
        if not is_admin_or_dept_admin(user): # <--- UPDATED CLEARANCE
            if not SubjectAllocation.objects.filter(staff__user=user, classroom=selected_class).exists():
                messages.error(request, "Permission Denied: You do not have subject allocations for this class.")
                return redirect('exam:teacher_select')

        # Filter subjects: Admins/Dept Heads see all, Teachers see only their assigned subjects
        if is_admin_or_dept_admin(user): # <--- UPDATED CLEARANCE
            subjects = selected_class.stream.subjects.all() if selected_class.stream else Subject.objects.all()
        else:
            subjects = Subject.objects.filter(
                id__in=SubjectAllocation.objects.filter(
                    staff__user=user, 
                    classroom=selected_class
                ).values_list('subject_id', flat=True)
            )

    return render(request, 'exam/teacher_select.html', {
        'exams': exams, 
        'classes': classes,
        'subjects': subjects,
        'selected_class_id': selected_class_id,
        'is_restricted': not is_admin_or_dept_admin(user) # <--- UPDATED CLEARANCE
    })

# --- 4. MARK ENTRY ---
@login_required
@user_passes_test(is_teacher)
def enter_marks(request, exam_id, class_id, subject_id):
    """ Grid entry for marks with built-in grade calculation preview """
    exam = get_object_or_404(Exam, id=exam_id)
    classroom = get_object_or_404(ClassRoom, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)

    # SECURE LOCK: Check if teacher is assigned to this exact class/subject pair
    if not is_admin_or_dept_admin(request.user): # <--- UPDATED CLEARANCE
        has_permission = SubjectAllocation.objects.filter(
            staff__user=request.user, 
            classroom=classroom, 
            subject=subject
        ).exists()
        
        if not has_permission:
            messages.error(request, "Security Violation: You are not authorized for this specific mark sheet.")
            return redirect('exam:teacher_select')

    if exam.is_locked:
        messages.error(request, "This exam session is locked and cannot be edited.")
        return redirect('exam:teacher_select')

    students = Student.objects.filter(classroom=classroom).select_related('user').order_by('roll_number')
    
    if request.method == 'POST':
        for student in students:
            mark_str = request.POST.get(f'mark_{student.id}')
            remark = request.POST.get(f'remark_{student.id}', '')
            
            # Update only if a value is provided; empty strings are ignored to allow partial entry
            if mark_str is not None and mark_str.strip() != "":
                try:
                    Result.objects.update_or_create(
                        exam=exam, student=student, subject=subject,
                        defaults={
                            'marks_obtained': float(mark_str),
                            'entered_by': request.user,
                            'remarks': remark
                        }
                    )
                except ValueError: 
                    continue 
                    
        messages.success(request, f"Marks successfully saved for {subject.name} ({classroom.name})")
        return redirect('exam:teacher_select')

    # Map existing results for the UI grid
    existing_results = Result.objects.filter(exam=exam, subject=subject, student__in=students)
    result_map = {r.student.id: r for r in existing_results}

    mark_entry_list = []
    for student in students:
        res = result_map.get(student.id)
        current_mark = res.marks_obtained if res else ''
        mark_entry_list.append({
            'student': student,
            'mark': current_mark,
            'remark': res.remarks if res else '',
            'grade': calculate_grade(current_mark)
        })

    return render(request, 'exam/mark_entry.html', {
        'exam': exam, 
        'classroom': classroom, 
        'subject': subject,
        'mark_entry_list': mark_entry_list
    })

# --- 5. ADMIN MANAGEMENT ---
@login_required
@user_passes_test(is_admin_or_dept_admin) # <--- UPDATED CLEARANCE
def create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New exam session created.")
            return redirect('exam:admin_dashboard')
    else:
        form = ExamForm()
    return render(request, 'exam/exam_form.html', {'form': form, 'title': 'Create Exam'})

@login_required
@user_passes_test(is_admin_or_dept_admin) # <--- UPDATED CLEARANCE
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam settings updated.")
            return redirect('exam:admin_dashboard')
    else:
        form = ExamForm(instance=exam)
    return render(request, 'exam/exam_form.html', {'form': form, 'title': 'Edit Exam'})