from django.urls import path
from . import views

app_name = 'admission'

urlpatterns = [
    # 1. LANDING PAGE / DASHBOARD
    path('', views.admission_list, name='index'), 
    
    # 2. APPLICATION FORMS
    path('apply/', views.public_apply_admission, name='apply'),                     # Guest Form (No Sidebar)
    path('internal-apply/', views.internal_apply_admission, name='internal_apply'), # Admin Form (With Sidebar)
    
    # 3. ADMISSION ACTIONS
    path('admit/<int:application_id>/', views.admit_student, name='admit_student'),
    path('reject/<int:pk>/', views.reject_application, name='reject'),
    
    # 4. UTILITIES
    path('setup-classrooms/', views.setup_classrooms, name='setup_classrooms'),
]