from django.urls import path
from . import views

app_name = 'lms'

urlpatterns = [
    # The Main Dashboard
    path('', views.index, name='index'), 
    
    # Course Management
    path('manage/directory/', views.admin_course_list, name='admin_course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('create/', views.create_course, name='create_course'),
    path('edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete/<int:course_id>/', views.delete_course, name='delete_course'),
    
    # Lessons
    path('course/<int:course_id>/add-lesson/', views.add_lesson, name='add_lesson'),
    path('lesson/<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('lesson/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    
    # Materials
    path('material/add/<int:course_id>/<int:lesson_id>/', views.add_material, name='add_material'),
    path('material/<int:material_id>/edit/', views.edit_material, name='edit_material'),
    path('material/<int:material_id>/delete/', views.delete_material, name='delete_material'),

    # Assignments & Grading (CRITICAL: Added these to fix the NoReverseMatch)
    path('assignment/add/<int:course_id>/', views.add_assignment, name='add_assignment'),
    path('assignment/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
]