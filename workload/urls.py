from django.urls import path
from . import views

app_name = 'workload'

urlpatterns = [
    # Admin Summary
    path('dashboard/', views.workload_dashboard, name='dashboard'),
    
    # Individual Detail
    path('teacher/<int:staff_id>/', views.teacher_detail, name='teacher_detail'),
    path('my-schedule/', views.my_workload, name='my_workload'),
]