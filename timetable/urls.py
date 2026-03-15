from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    # Main Navigation
    path('', views.index, name='index'),
    path('manage/', views.manage_timetable, name='manage_timetable'), 
    path('view/<int:classroom_id>/', views.view_timetable, name='view_timetable'),
    
    # Entry Management (Manual)
    path('add/<int:class_id>/<str:day>/<int:slot_id>/', views.add_entry, name='add_entry'),
    path('delete/<int:entry_id>/', views.delete_entry, name='delete_entry'),
    
    # --- Automated Actions (The "Magic" Buttons) ---
    path('auto-fill/<int:classroom_id>/', views.auto_fill_timetable, name='auto_fill'),
    path('clear/<int:classroom_id>/', views.clear_timetable, name='clear_timetable'),
    
    # Analytics & Reports
    path('workload/', views.teacher_workload_analysis, name='workload_analysis'),

    # AJAX Conflict Checkers (The "Smooth" Logic)
    path('check-drag-conflict/', views.check_drag_conflict, name='check_drag_conflict'),
    path('check-conflict/', views.check_teacher_conflict, name='check_teacher_conflict'),
    path('manage-class/', views.manage_class_timetable, name='manage_class'),
]