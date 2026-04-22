from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.urls import reverse

# --- IDENTITY & SECURITY INTEGRATION ---
from staff.decorators import allowed_users

# Import Models & Forms
from .models import AdmissionApplication, ClassRoom
from .forms import ApplicationForm
from student_info.models import Student 

# --- 1a. PUBLIC Apply View (For Guests) ---
def public_apply_admission(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        
        if form.is_valid():
            classroom = form.cleaned_data['class_applied']
            
            # Capacity Check
            if classroom.occupied_seats >= classroom.total_seats:
                messages.warning(request, f"{classroom.name} is full! Application placed on Waitlist.")
                status = 'Waitlist'
            else:
                status = 'Pending'

            app = form.save(commit=False)
            app.status = status
            app.save()
            
            messages.success(request, f"Application submitted! Ref ID: {app.id}. We will contact you soon.")
            return redirect('landing')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ApplicationForm()

    return render(request, 'admission/public_apply_admission.html', {'form': form})

# --- 1b. INTERNAL Apply View (Admin/Office Staff/Dept Admin) ---
@login_required
@allowed_users(allowed_roles=['Office_Staff', 'Admin', 'Dept_Admin'])
def internal_apply_admission(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        
        if form.is_valid():
            classroom = form.cleaned_data['class_applied']
            
            if classroom.occupied_seats >= classroom.total_seats:
                messages.warning(request, f"{classroom.name} is full! Application placed on Waitlist.")
                status = 'Waitlist'
            else:
                status = 'Pending'

            app = form.save(commit=False)
            app.status = status
            app.save()
            
            messages.success(request, f"Application successfully added! Ref ID: {app.id}")
            return redirect('admission:index')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ApplicationForm()

    return render(request, 'admission/internal_apply_admission.html', {'form': form})

# --- 2. Admin Dashboard (Admission List) ---
@login_required
@allowed_users(allowed_roles=['Office_Staff', 'Admin', 'Dept_Admin'])
def admission_list(request):
    applications = AdmissionApplication.objects.select_related('class_applied', 'stream_applied').all().order_by('-applied_date')
    classrooms = ClassRoom.objects.all().order_by('standard', 'division')
    
    stats = {
        'total': applications.count(),
        'pending': applications.filter(status='Pending').count(),
        'admitted': applications.filter(status='Admitted').count(),
        'rejected': applications.filter(status='Rejected').count(),
    }

    context = {
        'applications': applications,
        'classrooms': classrooms,
        'stats': stats
    }
    return render(request, 'admission/list.html', context)

# --- 3. Admit Student (Core Logic) ---
@login_required
@allowed_users(allowed_roles=['Office_Staff', 'Admin', 'Dept_Admin']) # <-- UPDATED CLEARANCE
@transaction.atomic 
def admit_student(request, application_id):
    app = get_object_or_404(AdmissionApplication, pk=application_id)
    target_class = app.class_applied

    if app.status == 'Admitted':
        msg = f"{app.student_name} is already admitted."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': msg})
        messages.warning(request, msg)
        return redirect('admission:index')
    
    if target_class.occupied_seats >= target_class.total_seats:
        msg = f"Cannot admit. {target_class.name} is full!"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': msg})
        messages.error(request, msg)
        return redirect('admission:index')

    try:
        # Generate Admission Number
        year = timezone.now().year
        last_student = Student.objects.filter(student_id__startswith=f"ADM{year}").order_by('student_id').last()
        
        if last_student:
            try:
                last_seq = int(last_student.student_id[-3:]) 
                new_seq = last_seq + 1
            except ValueError:
                new_seq = Student.objects.count() + 1
        else:
            new_seq = 1
            
        admission_no = f"ADM{year}{new_seq:03d}"

        # Create User Account
        clean_name = ''.join(e for e in app.student_name.split()[0] if e.isalnum()).lower()
        if not clean_name: clean_name = "student"
        
        username = f"{clean_name}.{new_seq:03d}"
        password = f"Welcome{year}" 
        
        if User.objects.filter(username=username).exists():
             username = f"{clean_name}.{new_seq:03d}.{timezone.now().strftime('%S')}"

        user = User.objects.create_user(username=username, email=app.email, password=password)
        user.first_name = app.student_name.split()[0]
        if len(app.student_name.split()) > 1:
            user.last_name = " ".join(app.student_name.split()[1:])
        user.save()
        
        # Identity Logic: The Profile signal will automatically handle Group assignment
        # However, we explicitly update the profile role to ensure correct provisioning
        user.profile.role = 'Student'
        user.profile.save()
        
        # Create Student Profile
        new_student = Student.objects.create(
            user=user,
            student_id=admission_no,
            classroom=target_class,
            stream=app.stream_applied,
            first_language=app.first_language,
            second_language=app.second_language,
            optional_subject=app.optional_subject, 
            father_name=app.parent_name,
            address=app.address,
            primary_phone=app.phone,
            emergency_phone=app.phone,
            gender=app.gender,
            date_of_birth=app.date_of_birth,
            photo=app.passport_photo,
            is_active=True,
            status='pursuing'
        )

        app.status = 'Admitted'
        app.admitted_student = user
        app.save()

        success_msg = f"Successfully Admitted! ID: {admission_no}"
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                profile_url = reverse('student_info:profile_view', args=[new_student.student_id])
            except:
                profile_url = "#"

            return JsonResponse({
                'status': 'success', 
                'message': success_msg,
                'username': username,
                'student_id': admission_no,
                'profile_url': profile_url
            })

        messages.success(request, success_msg)
        return redirect('admission:index')

    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        messages.error(request, f"Error: {str(e)}")
        return redirect('admission:index')

# --- 4. Reject Action ---
@login_required
@allowed_users(allowed_roles=['Office_Staff', 'Admin', 'Dept_Admin']) # <-- UPDATED CLEARANCE
def reject_application(request, pk):
    app = get_object_or_404(AdmissionApplication, pk=pk)
    
    if app.status == 'Admitted':
        messages.error(request, "Cannot reject an already admitted student.")
    else:
        app.status = 'Rejected'
        app.save()
        messages.info(request, f"Application for {app.student_name} Rejected.")
        
    return redirect('admission:index')

# --- 5. UTILITY: Setup Classrooms ---
@login_required
@allowed_users(allowed_roles=['Admin']) # Kept strictly for Root Admins
def setup_classrooms(request):
    batch_codes = [
        'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2', 
        'E1', 'E2', 'F1', 'F2', 'G1', 'G2', 'H1', 'H2', 
        'I1', 'I2', 'K1', 'K2'
    ]

    results = []
    for code in batch_codes:
        try:
            letter = code[0]
            number = code[1]
            if number == '1': std = '11'
            elif number == '2': std = '12'
            else: continue
                
            obj, created = ClassRoom.objects.get_or_create(
                standard=std, 
                division=letter,
                defaults={'total_seats': 60}
            )
            status = "CREATED" if created else "EXISTS"
            results.append(f"[{status}] Class {obj.name}")
        except Exception as e:
            results.append(f"[ERROR] Failed {code}: {str(e)}")

    return HttpResponse("<br>".join(results) + "<br><br><a href='/admission/'>Go to Dashboard</a>")