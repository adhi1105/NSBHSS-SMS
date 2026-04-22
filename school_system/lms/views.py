import csv
import io
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse

# Models
from .models import Course, Lesson, StudyMaterial, Stream, Assignment, LessonVideo, StudentSubmission
from student_info.models import Student
from admission.models import ClassRoom 
from school_system.models import Subject 
from staff.models import SubjectAllocation

# Forms
from .forms import CourseForm, StudyMaterialForm, AssignmentForm, LessonForm, VideoFormSet

# --- Security & Isolation Helpers ---

def is_admin_or_dept_admin(user):
    """Checks if the user has full administrative rights or is a Department Head."""
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Dept_Admin']).exists()

def is_staff(user):
    """Checks if the user has administrative or teaching privileges."""
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Dept_Admin', 'Staff', 'Teacher']).exists()

def get_teacher_allowed_classes(user):
    """
    Core Isolation Engine: Returns ClassRooms assigned to the teacher 
    via SubjectAllocation. Admins and Dept Admins see all classes.
    """
    if is_admin_or_dept_admin(user):
        return ClassRoom.objects.all()
    
    assigned_class_ids = SubjectAllocation.objects.filter(staff__user=user).values_list('classroom_id', flat=True)
    return ClassRoom.objects.filter(id__in=assigned_class_ids).distinct()

# --- 1. TRAFFIC CONTROLLER ---

@login_required
def index(request):
    user = request.user
    if is_staff(user):
        # Isolation: Admins/Dept Admins see all, Teachers see courses for their assigned classes
        allowed_classes = get_teacher_allowed_classes(user)
        
        if is_admin_or_dept_admin(user):
            courses = Course.objects.all().select_related('stream', 'classroom', 'teacher')
        else:
            # Mini-Admin: Teachers manage all courses within their assigned rooms
            courses = Course.objects.filter(classroom__in=allowed_classes).select_related('stream', 'classroom', 'teacher')

        # Grouping logic for UI categorization
        courses_by_stream = {}
        for course in courses:
            stream_name = course.stream.name if course.stream else "General / Common"
            if stream_name not in courses_by_stream:
                courses_by_stream[stream_name] = []
            courses_by_stream[stream_name].append(course)

        return render(request, 'lms/course_list.html', {
            'courses_by_stream': courses_by_stream,
            'classrooms': allowed_classes,
            'is_manager': True # Triggers management UI in template
        })
    else:
        # STUDENT VIEW: Strictly isolated to their specific classroom
        try:
            student = Student.objects.get(user=user)
            my_courses = Course.objects.filter(classroom=student.classroom).select_related('teacher')
            upcoming_assignments = Assignment.objects.filter(
                course__in=my_courses,
                due_date__gte=timezone.now()
            ).order_by('due_date')[:5]

            context = {
                'courses': my_courses,
                'assignments': upcoming_assignments,
                'student': student
            }
            return render(request, 'lms/student_index.html', context)
        except Student.DoesNotExist:
            return render(request, 'error.html', {'message': "Student Profile Not Found"})

# --- 2. COURSE DETAIL ---

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    allowed_classes = get_teacher_allowed_classes(request.user)
    
    if is_staff(request.user):
        # Teacher Security: Verify the course belongs to an assigned classroom
        if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
            messages.error(request, "Access Denied: You are not assigned to this classroom.")
            return redirect('lms:index')
    else:
        # Student Security
        try:
            student = Student.objects.get(user=request.user)
            if course.classroom != student.classroom:
                messages.error(request, "Access Denied: Course not in your curriculum.")
                return redirect('lms:index')
        except Student.DoesNotExist:
             return render(request, 'error.html', {'message': "Student Profile Not Found"})

    return render(request, 'lms/course_detail.html', {'course': course})

# --- 3. ADMIN TOOLS & COURSE CREATION ---

@login_required
@user_passes_test(is_staff)
def admin_course_list(request):
    """Directory view filtered by teacher's assigned classes."""
    allowed_classes = get_teacher_allowed_classes(request.user).order_by('standard', 'division')

    selected_class_id = request.GET.get('class_id')
    selected_classroom = None
    subjects = []

    if selected_class_id:
        selected_classroom = get_object_or_404(allowed_classes, id=selected_class_id)
        
        # Filter subjects teacher is allocated to in this class
        if is_admin_or_dept_admin(request.user):
            subjects = Subject.objects.filter(Q(streams=selected_classroom.stream) | Q(subject_type__in=['Language', 'Common']))
        else:
            subjects = Subject.objects.filter(
                id__in=SubjectAllocation.objects.filter(
                    staff__user=request.user, classroom=selected_classroom
                ).values_list('subject_id', flat=True)
            ).distinct()

    return render(request, 'lms/admin_course_list.html', {
        'classrooms': allowed_classes,
        'selected_classroom': selected_classroom,
        'courses': subjects,
    })

@login_required
@user_passes_test(is_staff)
def create_course(request):
    allowed_classes = get_teacher_allowed_classes(request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            
            # Security check: Ensure teacher isn't spoofing a classroom ID
            if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
                messages.error(request, "Unauthorized classroom selection.")
                return redirect('lms:index')
                
            course.teacher = request.user
            course.save()
            messages.success(request, f"Course '{course.title}' created successfully!")
            return redirect('lms:index')
    else:
        form = CourseForm()
        form.fields['classroom'].queryset = allowed_classes
    
    return render(request, 'lms/course_form.html', {'form': form, 'title': 'Create New Course'})

@login_required
@user_passes_test(is_staff)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    allowed_classes = get_teacher_allowed_classes(request.user)

    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
         messages.error(request, "Access Denied: You do not have permission for this course.")
         return redirect('lms:index')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully!")
            return redirect('lms:index')
    else:
        form = CourseForm(instance=course)
        form.fields['classroom'].queryset = allowed_classes

    return render(request, 'lms/course_form.html', {'form': form, 'title': 'Edit Course'})

@login_required
@user_passes_test(is_staff)
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    allowed_classes = get_teacher_allowed_classes(request.user)

    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
         messages.error(request, "Access Denied.")
         return redirect('lms:index')
    
    course.delete()
    messages.success(request, "Course removed.")
    return redirect('lms:index')

# --- 4. LESSON MANAGEMENT (MULTI-VIDEO SUPPORT) ---

@login_required
@user_passes_test(is_staff)
def add_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    allowed_classes = get_teacher_allowed_classes(request.user)
    
    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
        messages.error(request, "Unauthorized access.")
        return redirect('lms:index')

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        formset = VideoFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            
            if not lesson.order:
                last_lesson = Lesson.objects.filter(course=course).order_by('-order').first()
                lesson.order = (last_lesson.order + 1) if last_lesson else 1

            lesson.save()
            formset.instance = lesson
            formset.save()
            
            messages.success(request, f"Lesson '{lesson.title}' added!")
            return redirect('lms:course_detail', course_id=course.id)
    else:
        next_order = Lesson.objects.filter(course=course).count() + 1
        form = LessonForm(initial={'order': next_order})
        formset = VideoFormSet()

    return render(request, 'lms/lesson_form.html', {
        'form': form, 'formset': formset, 'course': course, 'title': 'Add Lesson'
    })

@login_required
@user_passes_test(is_staff)
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    allowed_classes = get_teacher_allowed_classes(request.user)
    
    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
        messages.error(request, "Access Denied.")
        return redirect('lms:index')

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        formset = VideoFormSet(request.POST, instance=lesson)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Lesson updated.")
            return redirect('lms:course_detail', course_id=course.id)
    else:
        form = LessonForm(instance=lesson)
        formset = VideoFormSet(instance=lesson)

    return render(request, 'lms/lesson_form.html', {
        'form': form, 'formset': formset, 'course': course, 'title': 'Edit Lesson'
    })

@login_required
@user_passes_test(is_staff)
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    allowed_classes = get_teacher_allowed_classes(request.user)

    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
        messages.error(request, "Access Denied.")
        return redirect('lms:index')
    
    lesson.delete()
    messages.success(request, "Lesson removed.")
    return redirect('lms:course_detail', course_id=course.id)

# --- 5. MATERIALS & ASSIGNMENTS ---

@login_required
@user_passes_test(is_staff)
def add_material(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id)
    allowed_classes = get_teacher_allowed_classes(request.user)

    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
        return redirect('lms:index')
    
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.lesson = lesson
            material.save()
            messages.success(request, "Material uploaded.")
            return redirect('lms:course_detail', course_id=course.id)
    else:
        form = StudyMaterialForm()
    return render(request, 'lms/form_modal.html', {'form': form, 'title': 'Add Material'})

@login_required
@user_passes_test(is_staff)
def edit_material(request, material_id):
    material = get_object_or_404(StudyMaterial, id=material_id)
    course = material.lesson.course
    allowed_classes = get_teacher_allowed_classes(request.user)
    
    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
        messages.error(request, "Access Denied.")
        return redirect('lms:index')

    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, "Material updated.")
            return redirect('lms:course_detail', course_id=course.id)
    else:
        form = StudyMaterialForm(instance=material)

    return render(request, 'lms/form_modal.html', {'form': form, 'title': 'Edit Material'})

@login_required
@user_passes_test(is_staff)
def delete_material(request, material_id):
    material = get_object_or_404(StudyMaterial, id=material_id)
    course = material.lesson.course
    allowed_classes = get_teacher_allowed_classes(request.user)

    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
        messages.error(request, "Access Denied.")
        return redirect('lms:index')
    
    material.delete()
    messages.success(request, "Material removed.")
    return redirect('lms:course_detail', course_id=course.id)

@login_required
@user_passes_test(is_staff)
def add_assignment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    allowed_classes = get_teacher_allowed_classes(request.user)

    if not is_admin_or_dept_admin(request.user) and course.classroom not in allowed_classes:
        messages.error(request, "Unauthorized.")
        return redirect('lms:index')

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assign = form.save(commit=False)
            assign.course = course
            assign.save()
            messages.success(request, "Assignment scheduled.")
            return redirect('lms:course_detail', course_id=course.id)
    else:
        form = AssignmentForm()
    return render(request, 'lms/form_modal.html', {'form': form, 'title': 'New Assignment'})

# --- 6. GRADING INTERFACE ---

@login_required
@user_passes_test(is_staff)
def assignment_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    allowed_classes = get_teacher_allowed_classes(request.user)

    # Isolation Check
    if not is_admin_or_dept_admin(request.user) and assignment.course.classroom not in allowed_classes:
        messages.error(request, "Access Denied.")
        return redirect('lms:index')

    # Get all students in this classroom and their submissions
    students = Student.objects.filter(classroom=assignment.course.classroom).select_related('user')
    submissions = StudentSubmission.objects.filter(assignment=assignment).select_related('student__user')

    # Create a mapping for easy lookup in template
    submission_map = {sub.student.id: sub for sub in submissions}

    return render(request, 'lms/submissions_list.html', {
        'assignment': assignment,
        'students': students,
        'submission_map': submission_map,
        'today': timezone.now()
    })

@login_required
@user_passes_test(is_staff)
def grade_submission(request, submission_id):
    submission = get_object_or_404(StudentSubmission, id=submission_id)
    allowed_classes = get_teacher_allowed_classes(request.user)

    if not is_admin_or_dept_admin(request.user) and submission.assignment.course.classroom not in allowed_classes:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        marks = request.POST.get('marks')
        remarks = request.POST.get('remarks')
        
        submission.marks_obtained = marks
        submission.teacher_remarks = remarks
        submission.graded_at = timezone.now()
        submission.status = 'graded'
        submission.save()

        messages.success(request, f"Graded {submission.student.user.get_full_name()}")
        return redirect('lms:assignment_submissions', assignment_id=submission.assignment.id)