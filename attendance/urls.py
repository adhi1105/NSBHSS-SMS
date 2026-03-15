from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # 1. Main Dashboard (THIS WAS MISSING)
    path('', views.index, name='index'),

    # 2. Select Class
    path('select-class/', views.select_class, name='select_class'),
    
    # 3. Mark Attendance
    path('mark/<int:classroom_id>/', views.mark_attendance, name='mark_attendance'),
    
    # 4. View History
    path('history/<int:classroom_id>/', views.view_history, name='history'),
    
    # 5. View Specific Date Report
    path('report/<int:classroom_id>/<str:date>/', views.view_date_report, name='date_report'),
    
]