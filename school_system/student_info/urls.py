from django.urls import path
from . import views

app_name = 'student_info'

urlpatterns = [
    # 1. Dashboard / Directory
    path('', views.student_list, name='index'),

    # 2. View Profile
    path('profile/<str:student_id>/', views.student_profile, name='profile_view'),

    # 3. Edit Profile
    path('edit/<str:student_id>/', views.edit_student, name='edit'),
    path('import/', views.import_students, name='import_students'),
    path('delete/<str:student_id>/', views.delete_student, name='delete_student'),
]