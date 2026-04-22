from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime

# --- SAFE IMPORTS ---
from student_info.models import Student
from staff.models import Staff
from timetable.models import TimetableEntry
from admission.models import ClassRoom, AdmissionApplication

# --- OPTIONAL MODULE IMPORTS (For Rich Dashboard Data) ---
try:
    from attendance.models import AttendanceRecord
except ImportError:
    AttendanceRecord = None

try:
    from fees.models import Payment, StudentFee
except ImportError:
    Payment = None
    StudentFee = None

try:
    from transportation.models import Vehicle, TransportSubscription
except ImportError:
    Vehicle = None
    TransportSubscription = None

try:
    from library.models import Issue
except ImportError:
    Issue = None

try:
    from lms.models import Course, Stream
except ImportError:
    Course = None
    Stream = None


# ==========================================
# 1. PUBLIC LANDING PAGE
# ==========================================
def main_landing(request):
    """
    The pre-login common landing page.
    Redirects authenticated users to their respective dashboards automatically.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    return render(request, 'landing.html')


# ==========================================
# 2. MAIN DASHBOARD DISPATCHER
# ==========================================
@login_required(login_url='login')
def home(request):
    """
    The Main Dashboard Dispatcher.
    Routes users to their specialized portal based on their Identity Registry Group.
    """
    user = request.user
    today = timezone.now().date()
    
    # Extract the user's primary group role
    user_group = user.groups.first().name if user.groups.exists() else None
    
    # ---------------------------------------------------------
    # A. ROOT ADMIN DASHBOARD (ANALYTICS ENGINE)
    # ---------------------------------------------------------
    if user.is_superuser or user_group == 'Admin':
        # Admission Analytics
        admission_stats = {'pending': 0, 'approved': 0, 'admitted': 0, 'total_new': 0}
        if AdmissionApplication:
            admissions = AdmissionApplication.objects.all()
            admission_stats = {
                'pending': admissions.filter(status='Pending').count(),
                'approved': admissions.filter(status='Approved').count(),
                'admitted': admissions.filter(status='Admitted').count(),
                'total_new': admissions.filter(applied_date__date=today).count()
            }

        # Finance Analytics
        total_fees = 0
        if Payment:
            total_fees = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Attendance Pulse (Real-time)
        present_today = 0
        if AttendanceRecord:
            present_today = AttendanceRecord.objects.filter(log__date=today, status='present').count()

        # Logistics & Library Pulse
        active_vehicles = Vehicle.objects.filter(is_active=True).count() if Vehicle else 0
        books_out = Issue.objects.filter(is_returned=False).count() if Issue else 0
        
        # Core System Stats
        course_count = Course.objects.count() if Course else 0
        stream_count = Stream.objects.count() if Stream else 0
        class_count = ClassRoom.objects.count()
        active_staff_count = Staff.objects.filter(user__is_active=True).count()

        context = {
            'student_count': Student.objects.count(),
            'staff_count': active_staff_count,
            'total_fees': total_fees,
            'active_vehicles': active_vehicles,
            'course_count': course_count,
            'stream_count': stream_count,
            'class_count': class_count,
            'admission_stats': admission_stats,
            'present_today': present_today,
            'books_out': books_out,
            'today': timezone.now()
        }
        return render(request, 'dashboard_admin.html', context)

    # ---------------------------------------------------------
    # B. DYNAMIC STAFF ROUTING (New Identity Nodes)
    # ---------------------------------------------------------
    elif user_group == 'Teacher':
        return redirect('staff:teacher_portal')
        
    elif user_group in ['Cashier', 'Librarian', 'Office_Staff', 'Dept_Admin']:
        # Unified context payload for specialized dashboards
        context = {
            'role': user_group,
            'today': today,
        }
        
        if user_group == 'Cashier':
            context['node_title'] = "Finance & Fee Operations"
            context['node_id'] = "FIN_NODE_01"
            context['icon'] = "bi-wallet2"
            context['stat_1_label'] = "Today's Collection"
            # FIX: Changed payment_date to date to match the Payment model
            context['stat_1_val'] = f"₹{Payment.objects.filter(date=today).aggregate(Sum('amount'))['amount__sum'] or 0}" if Payment else "₹0"
            context['stat_2_label'] = "Pending Dues Overview"
            context['stat_2_val'] = f"₹{StudentFee.objects.aggregate(Sum('balance'))['balance__sum'] or 0}" if StudentFee else "₹0"
            context['primary_link'] = 'fees:index'
            context['primary_action'] = "Open Ledger"
            
        elif user_group == 'Librarian':
            context['node_title'] = "Library Circulation Desk"
            context['node_id'] = "LIB_NODE_02"
            context['icon'] = "bi-book"
            context['stat_1_label'] = "Books Currently Out"
            context['stat_1_val'] = Issue.objects.filter(is_returned=False).count() if Issue else 0
            context['stat_2_label'] = "Overdue Returns"
            context['stat_2_val'] = Issue.objects.filter(is_returned=False, due_date__lt=today).count() if Issue else 0
            context['primary_link'] = 'library:index'
            context['primary_action'] = "Manage Circulation"
            
        elif user_group == 'Office_Staff':
            context['node_title'] = "Front Desk & Operations"
            context['node_id'] = "OPS_NODE_03"
            context['icon'] = "bi-building"
            context['stat_1_label'] = "Pending Admissions"
            context['stat_1_val'] = AdmissionApplication.objects.filter(status='Pending').count() if AdmissionApplication else 0
            context['stat_2_label'] = "Active Students"
            context['stat_2_val'] = Student.objects.filter(user__is_active=True).count()
            context['primary_link'] = 'admission:index'
            context['primary_action'] = "Open Admissions"
            
        elif user_group == 'Dept_Admin':
            context['node_title'] = "Department Control Center"
            context['node_id'] = "DEPT_NODE_04"
            context['icon'] = "bi-diagram-3"
            context['stat_1_label'] = "Total Faculty"
            context['stat_1_val'] = Staff.objects.filter(user__is_active=True).count()
            context['stat_2_label'] = "Active Classrooms"
            context['stat_2_val'] = ClassRoom.objects.count()
            context['primary_link'] = 'staff:staff_list'
            context['primary_action'] = "Manage Faculty"

        return render(request, 'dashboard_specialized.html', context)

    # ---------------------------------------------------------
    # C. STUDENT DASHBOARD (PERSONALIZED VIEW)
    # ---------------------------------------------------------
    elif user_group == 'Student':
        try:
            # select_related optimizes queries for classroom and user profile data
            student = Student.objects.select_related('classroom', 'user').get(user=user)
            
            now = datetime.now()
            today_name = now.strftime('%A')
            current_time = now.time()
            
            # Optimized Timetable Logic (N+1 query protection)
            timetable_qs = TimetableEntry.objects.select_related('subject', 'staff__user').filter(
                classroom=student.classroom,
                day=today_name
            )

            current_class = timetable_qs.filter(
                time_slot__start_time__lte=current_time,
                time_slot__end_time__gte=current_time
            ).first()

            next_class = timetable_qs.filter(
                time_slot__start_time__gt=current_time
            ).order_by('time_slot__start_time').first()

            # Library Status
            overdue_books = []
            if Issue:
                overdue_books = Issue.objects.filter(
                    student=student, 
                    is_returned=False, 
                    due_date__lt=today
                ).select_related('book')[:3]

            # Transport Status Check
            transport_status = "Not Subscribed"
            if TransportSubscription:
                sub = TransportSubscription.objects.filter(student=student, is_active=True).first()
                if sub: transport_status = "Active"

            # Personal Attendance Analytics
            attendance_percentage = 0
            total_days = 0
            present_days = 0
            if AttendanceRecord:
                records = AttendanceRecord.objects.filter(student=student)
                total_days = records.count()
                present_days = records.filter(status='present').count()
                if total_days > 0:
                    attendance_percentage = round((present_days / total_days) * 100, 1)

            # Personal Finance Status
            fees_due = 0
            if StudentFee:
                fees_due = StudentFee.objects.filter(student=student).aggregate(Sum('balance'))['balance__sum'] or 0

            context = {
                'student': student,
                'current_class': current_class,
                'next_class': next_class,
                'attendance_percentage': attendance_percentage,
                'total_days': total_days,
                'present_days': present_days,
                'fees_due': fees_due,
                'overdue_books': overdue_books,
                'transport_status': transport_status,
                'today': today,
            }
            return render(request, 'dashboard_student.html', context)
            
        except Student.DoesNotExist:
            # Route unassigned students to the Onboarding Terminal instead of an error
            context = {
                'title': 'Student Onboarding',
                'status_code': 'AWAITING_CLASS_ASSIGNMENT',
                'message': 'Your account has been verified. Please wait while the Administration assigns you to a Class Node.',
            }
            return render(request, 'dashboard_new_user.html', context)
    
    # ---------------------------------------------------------
    # D. FINAL FALLBACK (Unassigned / Ghost Accounts)
    # ---------------------------------------------------------
    else:
        # Route users with absolutely no roles to the Onboarding Terminal
        context = {
            'title': 'Identity Provisioning',
            'status_code': 'PENDING_CLEARANCE',
            'message': 'Your identity has been registered in the system, but you have not been granted access clearances yet.',
        }
        return render(request, 'dashboard_new_user.html', context)


# ==========================================
# 3. AUTHENTICATION & REGISTRATION
# ==========================================
def register(request):
    if request.user.is_authenticated:
        return redirect('home')
        
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
        
    # Updated to use the custom template
    return render(request, 'auth/register.html', {'form': form})


def password_reset_contact(request):
    """
    Instructions for users who forgot their credentials.
    """
    return render(request, 'password_reset_contact.html')