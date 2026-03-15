from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # --- 0. THE TEACHER PORTAL & TOOLS ---
    path('dashboard_teacher/', views.teacher_portal, name='teacher_portal'),
    path('my-timetable/', views.teacher_timetable, name='teacher_timetable'),

    # 1. Main Staff Directory
    path('', views.staff_list, name='staff_list'),
    path('index/', views.staff_list, name='index'), 
    path('dashboard/', views.staff_list, name='staff_dashboard'), # Added for consistency

    # --- STAFF PROFILE & ROLE MANAGEMENT ---
    path('profile/<int:staff_id>/', views.staff_detail, name='staff_detail'),
    # NEW: URL to change roles directly from the Web App Dashboard
    path('sync-role/<int:staff_id>/', views.sync_staff_roles, name='sync_staff_roles'),
    # NEW: URL for Nuclear Role Repair
    path('repair-roles/', views.repair_stuck_roles, name='repair_stuck_roles'),

    # 2. Onboarding
    path('add/', views.add_staff, name='add'),

    # 3. Subject Allocation
    path('allocation/', views.allocate_subject, name='allocation_list'),
    path('allocation/delete/<int:allocation_id>/', views.delete_allocation, name='delete_allocation'),

    # 5. Workload Analytics & AUTO-MAINTENANCE
    path('workload/', views.workload_dashboard, name='workload'),
    
    # NEW: The Auto-Distribute Button URL
    path('workload/auto-distribute/', views.auto_distribute_workload, name='auto_distribute'),

    # --- 6. CLASS TEACHER MANAGEMENT ---
    path('assign-teacher/', views.assign_class_teacher, name='assign_class_teacher'),
    # NEW: The Auto-Assign Class Teacher URL
    path('assign-teacher/auto/', views.auto_assign_class_teachers, name='auto_assign_class_teachers'),
    path('remove-teacher/<int:class_id>/', views.remove_class_teacher, name='remove_class_teacher'),
    path('promotion/', views.promotion_terminal, name='promotion_terminal'),

    path('dashboard/library/', views.librarian_dashboard, name='librarian_dashboard'),
    path('dashboard/finance/', views.cashier_dashboard, name='cashier_dashboard'),
    path('dashboard/office/', views.office_staff_dashboard, name='office_dashboard'),
    path('dashboard/department/', views.dept_admin_dashboard, name='dept_admin_dashboard'),
    path('admission/portal/', views.guest_dashboard, name='guest_dashboard'),
]