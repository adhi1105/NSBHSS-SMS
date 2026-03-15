from django.urls import path
from . import views

app_name = 'exam'

urlpatterns = [
    path('', views.entry_index, name='entry_index'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # NEW PATHS
    path('create/', views.create_exam, name='create_exam'),
    path('edit/<int:exam_id>/', views.edit_exam, name='edit_exam'),
    
    path('marks/select/', views.teacher_select, name='teacher_select'),
    path('marks/enter/<int:exam_id>/<int:class_id>/<int:subject_id>/', views.enter_marks, name='enter_marks'),
]