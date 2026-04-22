from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from .forms import UserRegisterForm

# --- SAFE IMPORTS ---
from student_info.models import Student
from staff.models import Staff, SubjectAllocation
from timetable.models import TimetableEntry
from admission.models import ClassRoom, AdmissionApplication

# --- OPTIONAL MODULE IMPORTS ---
try:
    from attendance.models import Attendance, AttendanceRecord, AttendanceLog
except ImportError:
    Attendance = AttendanceRecord = AttendanceLog = None

try:
    from fees.models import Payment, StudentFee
except ImportError:
    Payment = StudentFee = None

try:
    from transportation.models import Vehicle, TransportSubscription
except ImportError:
    Vehicle = TransportSubscription = None

try:
    from library.models import Issue, Book
except ImportError:
    Issue = Book = None

try:
    from lms.models import Course, Stream
except ImportError:
    Course = Stream = None


# ==========================================
# 1. PROFILE VIEW
# ==========================================
@login_required
def my_profile(request):
    user = request.user
    context = {'user': user}

    if hasattr(user, 'student') or hasattr(user, 'student_profile'):
        try:
            student = getattr(user, 'student', None) or getattr(user, 'student_profile', None)
            if not student:
                student = Student.objects.get(user=user)
                
            context['profile'] = student
            context['role'] = 'Student'
            context['academic'] = {
                'class': student.classroom,
                'stream': getattr(student, 'stream', None),
                'subjects': [
                    getattr(student, 'first_language', '-'), 
                    getattr(student, 'second_language', '-'), 
                    getattr(student, 'optional_subject', '-')
                ]
            }
            return render(request, 'profile.html', context)
        except Student.DoesNotExist:
            pass

    if hasattr(user, 'staff'):
        try:
            staff = user.staff
            context['profile'] = staff
            context['role'] = 'Staff'
            return render(request, 'profile.html', context)
        except Staff.DoesNotExist:
            pass

    if user.is_superuser or user.groups.filter(name='Admin').exists():
        context['role'] = 'Administrator'
        active_users = User.objects.filter(is_active=True).select_related('staff').order_by('-date_joined')[:50]
        
        user_list = []
        for u in active_users:
            role_display = "User"
            if hasattr(u, 'staff'): role_display = "Staff"
            elif hasattr(u, 'student'): role_display = "Student"
            elif u.is_superuser: role_display = "Admin"
            
            user_list.append({
                'id': u.id, 'username': u.username, 'email': u.email,
                'role': role_display, 'joined': u.date_joined,
            })
            
        context['admin_user_list'] = user_list
        return render(request, 'profile.html', context)

    context['role'] = 'User'
    return render(request, 'profile.html', context)


# ==========================================
# 2. MAIN DASHBOARD DISPATCHER (The 'Home' View)
# ==========================================
@login_required
def home(request):
    user = request.user
    today = timezone.now().date()
    stats = {} # Adaptive Analytics Container

    # ---------------------------------------------------------
    # A. ADMIN DASHBOARD ANALYTICS
    # ---------------------------------------------------------
    if user.is_superuser or user.groups.filter(name='Admin').exists():
        # 1. Admission Analytics
        admission_stats = {'pending': 0, 'approved': 0, 'admitted': 0}
        if AdmissionApplication:
            admissions = AdmissionApplication.objects.all()
            admission_stats = {
                'pending': admissions.filter(status='Pending').count(),
                'approved': admissions.filter(status='Approved').count(),
                'admitted': admissions.filter(status='Admitted').count(),
                'total_new': admissions.filter(applied_date__date=today).count()
            }

        # 2. Finance Analytics
        total_revenue = 0
        if Payment:
            total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0

        # 3. Attendance Analytics (Global Pulse)
        present_today = 0
        if AttendanceRecord:
            present_today = AttendanceRecord.objects.filter(log__date=today, status='present').count()

        # 4. Library Analytics
        books_out = 0
        if Issue:
            books_out = Issue.objects.filter(is_returned=False).count()

        context = {
            'student_count': Student.objects.count(),
            'staff_count': Staff.objects.filter(user__is_active=True).count(),
            'total_fees': total_revenue,
            'admission_stats': admission_stats,
            'class_count': ClassRoom.objects.count(),
            'present_today': present_today,
            'books_out': books_out,
            'today': timezone.now()
        }
        return render(request, 'dashboard_admin.html', context)

    # ---------------------------------------------------------
    # B. TEACHER DASHBOARD (REDIRECT)
    # ---------------------------------------------------------
    elif hasattr(user, 'staff') or user.groups.filter(name='Teacher').exists():
        # The teacher analytics are handled within the staff:teacher_portal view
        return redirect('staff:teacher_portal')

    # ---------------------------------------------------------
    # C. STUDENT DASHBOARD ANALYTICS
    # ---------------------------------------------------------
    elif hasattr(user, 'student') or hasattr(user, 'student_profile') or user.groups.filter(name='Student').exists():
        try:
            student = getattr(user, 'student', None) or getattr(user, 'student_profile', None)
            if not student:
                student = Student.objects.get(user=user)

            classroom = student.classroom
            now = datetime.now()
            today_name = now.strftime('%A')
            current_time = now.time()

            # 1. Live Timetable Logic
            current_class = TimetableEntry.objects.filter(
                classroom=classroom,
                day=today_name,
                time_slot__start_time__lte=current_time,
                time_slot__end_time__gte=current_time
            ).select_related('subject', 'staff__user').first()

            next_class = TimetableEntry.objects.filter(
                classroom=classroom, 
                day=today_name,
                time_slot__start_time__gt=current_time
            ).order_by('time_slot__start_time').first()

            # 2. Library Analytics (Personal)
            overdue_books = []
            if Issue:
                overdue_books = Issue.objects.filter(
                    student=student, 
                    is_returned=False, 
                    due_date__lt=today
                ).select_related('book')[:3]

            # 3. Transport Analytics
            transport_status = "Not Subscribed"
            if TransportSubscription:
                sub = TransportSubscription.objects.filter(student=student, is_active=True).first()
                if sub: transport_status = "Active"
            
            # 4. Personal Attendance Analytics
            attendance_percentage = 0
            total_days = 0
            present_days = 0
            if AttendanceRecord:
                records = AttendanceRecord.objects.filter(student=student)
                total_days = records.count()
                present_days = records.filter(status='present').count()
            elif Attendance: 
                records = Attendance.objects.filter(student=student)
                total_days = records.count()
                present_days = records.filter(status='Present').count()
                
            if total_days > 0:
                attendance_percentage = round((present_days / total_days) * 100, 1)

            # 5. Finance Analytics (Personal Balance)
            fees_due = 0
            if StudentFee:
                fees_due = StudentFee.objects.filter(student=student).aggregate(Sum('balance'))['balance__sum'] or 0
            
            context = {
                'student': student,
                'current_class': current_class,
                'next_class': next_class,
                'overdue_books': overdue_books,
                'transport_status': transport_status, 
                'attendance_percentage': attendance_percentage, 
                'total_days': total_days,
                'present_days': present_days,
                'fees_due': fees_due
            }
            return render(request, 'dashboard_student.html', context)
        except Student.DoesNotExist:
            return render(request, 'error.html', {'message': "Student Profile Not Found"})
    
    return render(request, 'error.html', {'message': "Account Setup Incomplete. Please contact Admin."})


# ==========================================
# 3. API VIEW (Real-Time Updates)
# ==========================================
@login_required
def live_dashboard_stats(request):
    user = request.user
    data = {}

    if user.is_superuser or user.groups.filter(name='Admin').exists():
        data['role'] = 'admin'
        data['total_students'] = Student.objects.count()
        data['total_staff'] = Staff.objects.filter(user__is_active=True).count()
        data['active_vehicles'] = Vehicle.objects.filter(is_active=True).count() if Vehicle else 0

    elif hasattr(user, 'student') or hasattr(user, 'student_profile'):
        data['role'] = 'student'
        student = getattr(user, 'student', None) or getattr(user, 'student_profile', None)
        if student:
            if AttendanceRecord:
                total = AttendanceRecord.objects.filter(student=student).count()
                present = AttendanceRecord.objects.filter(student=student, status='present').count()
                data['attendance_pct'] = round((present / total) * 100, 1) if total > 0 else 0

    return JsonResponse(data)


# ==========================================
# 4. REGISTRATION & AUTH HELPERS
# ==========================================
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            student_group, _ = Group.objects.get_or_create(name='Student')
            user.groups.add(student_group)
            messages.success(request, f'Account created for {user.username}! You can now login.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def password_reset_contact(request):
    return render(request, 'password_reset_contact.html')