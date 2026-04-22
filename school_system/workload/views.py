from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from staff.models import Staff

# --- 1. ADMIN DASHBOARD ---
@login_required
def workload_dashboard(request):
    """
    Summary view for Admins to analyze the distribution of teaching loads
    across the entire faculty.
    """
    # Only Admins/Principals should see the summary of EVERYONE
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        # Smart Redirect: Send teacher to their own personal view instead of an error page
        try:
            teacher_profile = Staff.objects.get(user=request.user)
            return redirect('workload:teacher_detail', staff_id=teacher_profile.id)
        except Staff.DoesNotExist:
            return redirect('home')

    # Admin Logic: Fetch all teaching staff and count their subject allocations
    teachers = Staff.objects.filter(is_teaching_staff=True).annotate(
        subject_count=Count('allocations')
    ).order_by('-subject_count')
    
    context = {
        'teachers': teachers,
        'page_title': 'Teacher Workload Analysis'
    }
    return render(request, 'workload/dashboard.html', context)

# --- 2. INDIVIDUAL TEACHER DETAIL ---
@login_required
def teacher_detail(request, staff_id):
    """
    Detailed view showing specific subjects and classes assigned to a teacher.
    Used by Admins to inspect individuals and by the system as a personal profile.
    """
    teacher = get_object_or_404(Staff, id=staff_id)
    
    # Security Check: Verify if the user has permission to see this specific profile
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
    
    # If not admin, check if the logged-in user owns this profile
    if not is_admin:
        if teacher.user != request.user:
            return render(request, 'error.html', {
                'message': "Security Restriction: You are not authorized to view another teacher's workload."
            })

    # Fetch the allocations (Subjects assigned to this teacher)
    # Optimized with select_related to avoid multiple DB hits in the template loop
    allocations = teacher.allocations.all().select_related('subject', 'classroom')

    context = {
        'teacher': teacher,
        'allocations': allocations,
        'total_load': allocations.count(),
        'is_admin': is_admin
    }
    return render(request, 'workload/teacher_detail.html', context)

# --- 3. TEACHER'S SELF-VIEW ---
@login_required
def my_workload(request):
    """
    Primary view for a logged-in Teacher to see their own workload via the sidebar link.
    This safely routes the user to their specific data without needing an ID in the URL.
    """
    try:
        # Get the Staff profile linked to the current user
        teacher = Staff.objects.get(user=request.user)
        
        # Reuse the detail logic to ensure UI consistency
        allocations = teacher.allocations.all().select_related('subject', 'classroom')
        
        context = {
            'teacher': teacher,
            'allocations': allocations,
            'total_load': allocations.count(),
            'is_admin': False # Hide admin-only features/navigation
        }
        return render(request, 'workload/teacher_detail.html', context)
        
    except Staff.DoesNotExist:
        # Fallback if a non-staff user (like a student) tries to access this URL
        return render(request, 'error.html', {'message': "Staff profile not found. Access restricted to faculty."})