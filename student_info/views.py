import csv
import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

# Import Models
from .models import Student
from admission.models import ClassRoom 
from school_system.models import Stream
from staff.models import SubjectAllocation 

# Import Forms
from .forms import StudentEditForm, CSVUploadForm, StudentFilterForm

# --- Helper Logic ---
def is_admin(user):
    """Checks if the user has root administrative privileges."""
    return user.is_superuser or user.groups.filter(name='Admin').exists()

def has_full_directory_access(user):
    """
    NEW: Checks if the user is part of the expanded administrative nodes.
    Grants access to Admin, Department Heads, and Office Staff.
    """
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Dept_Admin', 'Office_Staff']).exists()

def get_teacher_context(user):
    """
    Core Isolation Engine: 
    Returns a tuple of (base_students, base_classrooms) restricted by teacher allocation.
    Teachers only see students in classrooms where they are assigned a subject.
    Admins, Dept Admins, and Office Staff see everything.
    """
    # UPDATED: Use the expanded access helper here so Dept Admins don't get trapped by Teacher logic
    if has_full_directory_access(user):
        return Student.objects.all(), ClassRoom.objects.all()
    
    # Identify classes assigned to this staff member
    assigned_classes = ClassRoom.objects.filter(
        id__in=SubjectAllocation.objects.filter(staff__user=user).values_list('classroom_id', flat=True)
    ).distinct()
    
    # Filter students belonging to those classes
    return Student.objects.filter(classroom__in=assigned_classes), assigned_classes

# --- 1. Student Directory (Isolated & Optimized) ---
@login_required
def student_list(request):
    """
    Displays the student directory. 
    Teachers see a filtered list; Admins/Staff see everything.
    """
    base_students_qs, base_classrooms_qs = get_teacher_context(request.user)
    
    # Pre-fetch related data for performance (prevents N+1 query issues)
    students = base_students_qs.select_related('user', 'classroom', 'stream').order_by(
        'classroom__standard', 'user__first_name'
    )
    
    # Inject restricted queryset into form dropdown for accurate filtering
    form = StudentFilterForm(request.GET)
    form.fields['class_room'].queryset = base_classrooms_qs.order_by('standard', 'division')

    if form.is_valid():
        query = form.cleaned_data.get('search_query')
        if query:
            students = students.filter(
                Q(student_id__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(father_name__icontains=query)
            )

        classroom = form.cleaned_data.get('class_room')
        if classroom:
            students = students.filter(classroom=classroom)

        stream = form.cleaned_data.get('stream')
        if stream:
            students = students.filter(stream=stream)

        status = form.cleaned_data.get('status')
        if status:
            students = students.filter(status=status)

    context = {
        'students': students,
        'form': form,
        'classrooms': base_classrooms_qs.order_by('standard'),
        'page_title': 'Student Directory',
        'count': students.count()
    }
    return render(request, 'student_info/list.html', context)

# --- 2. View Profile (With Security Enforcement) ---
@login_required
def student_profile(request, student_id):
    """
    View individual student details. 
    Security: get_object_or_404 uses the restricted context.
    """
    base_students_qs, _ = get_teacher_context(request.user)
    student = get_object_or_404(base_students_qs, student_id=student_id)
    
    return render(request, 'student_info/profile.html', {
        'student': student,
        'page_title': f"Profile - {student.user.get_full_name()}"
    })

# --- 3. Edit Profile (With Security Enforcement) ---
@login_required
def edit_student(request, student_id):
    """
    Edit student information.
    Accessible to Admins, Dept Admins, Office Staff, and Teachers (limited to their assigned students).
    """
    base_students_qs, _ = get_teacher_context(request.user)
    student = get_object_or_404(base_students_qs, student_id=student_id)

    if request.method == 'POST':
        form = StudentEditForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated profile for {student.user.get_full_name()}")
            return redirect('student_info:profile_view', student_id=student.student_id)
    else:
        form = StudentEditForm(instance=student)

    return render(request, 'student_info/edit.html', {
        'form': form,
        'student': student,
        'page_title': f"Edit - {student.student_id}"
    })

# --- 4. Bulk Import (Expanded to include Office Staff & Dept Admins) ---
@login_required
@user_passes_test(has_full_directory_access) # UPDATED: Allowed Dept Admin and Office Staff to import
def import_students(request):
    """
    Allows bulk creation of students via CSV.
    Uses database transactions to ensure data integrity.
    """
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                decoded_file = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string, delimiter=',')
                next(reader, None)  # Skip Header
            except Exception as e:
                messages.error(request, f"Error reading file: {e}")
                return redirect('student_info:import_students')

            success_count = 0
            error_count = 0
            
            with transaction.atomic():
                for row in reader:
                    try:
                        if len(row) < 5: continue
                        f_name, l_name, email, c_name, phone = [x.strip() for x in row[:5]]

                        if User.objects.filter(email=email).exists():
                            error_count += 1
                            continue

                        classroom = ClassRoom.objects.get(name__iexact=c_name)
                        username = f"{f_name.lower()}{phone[-4:]}"
                        
                        user = User.objects.create_user(
                            username=username, email=email, password="123",
                            first_name=f_name, last_name=l_name
                        )
                        
                        group, _ = Group.objects.get_or_create(name='Student')
                        user.groups.add(group)

                        Student.objects.create(
                            user=user, classroom=classroom,
                            student_id=f"STU{user.id:04d}", 
                            primary_phone=phone, address="Imported via CSV",
                            status='pursuing'
                        )
                        success_count += 1
                    except Exception:
                        error_count += 1
            
            messages.info(request, f"Import Finished. Success: {success_count}, Failed: {error_count}")
            return redirect('student_info:index')
    else:
        form = CSVUploadForm()
    return render(request, 'student_info/import_csv.html', {'form': form, 'page_title': 'Bulk Import'})

# --- 5. Delete Profile (Kept Strictly Admin Only) ---
@login_required
@user_passes_test(is_admin) # Kept strictly for Root Admins as a safety measure
def delete_student(request, student_id):
    """
    Deletes both the Student profile and the associated User account.
    """
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == 'POST':
        name = student.user.get_full_name()
        user = student.user
        with transaction.atomic():
            student.delete()
            user.delete()
        messages.success(request, f"Permanently deleted record for {name}.")
        return redirect('student_info:index')
    return redirect('student_info:profile_view', student_id=student_id)