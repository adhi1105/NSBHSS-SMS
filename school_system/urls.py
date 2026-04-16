from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView, TemplateView

# Importing from your Root views.py (school_system/views.py)
from . import views as core_views 
# Import the SecureLoginForm we just created for the CAPTCHA
from .forms import SecureLoginForm 

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- 1. PUBLIC ENTRY POINT ---
    path('', core_views.main_landing, name='landing'),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),

    # --- 2. CORE AUTHENTICATION ---
    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html',
        authentication_form=SecureLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    
    path('register/', core_views.register, name='register'),

    # --- 3. INTERNAL ROUTING ---
    path('home/', core_views.home, name='home'),
    path('accounts/profile/', RedirectView.as_view(pattern_name='home')),
    path('accounts/login/', RedirectView.as_view(pattern_name='login')),
    path('dashboard/main/', RedirectView.as_view(pattern_name='home')),

    # --- 4. MODULAR APP ARCHITECTURE ---
    path('dashboard/', include('dashboard.urls')),
    path('staff/', include('staff.urls', namespace='staff')), 
    path('student_info/', include('student_info.urls', namespace='student_info')),
    path('admission/', include('admission.urls', namespace='admission')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('fees/', include('fees.urls', namespace='fees')),
    path('library/', include('library.urls', namespace='library')),
    path('transportation/', include('transportation.urls', namespace='transportation')),
    path('workload/', include('workload.urls', namespace='workload')),
    path('form_builder/', include('form_builder.urls', namespace='form_builder')),
    path('lms/', include('lms.urls', namespace='lms')),
    path('exam/', include('exam.urls', namespace='exam')),
    path('timetable/', include('timetable.urls', namespace='timetable')),
    path('communication/', include('communication.urls', namespace='communication')),
    path('captcha/', include('captcha.urls')),

    # --- 5. PASSWORD RESET FLOW (RE-SYNKED) ---
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset_form.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html',
        success_url='/password-reset-complete/'
    ), name='password_reset_confirm'),
    
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),
]