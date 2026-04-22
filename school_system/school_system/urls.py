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
    # The Root is now the Landing Page for all logged-out users
    path('', core_views.main_landing, name='landing'),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),

    # --- 2. CORE AUTHENTICATION ---
    # Updated to use the custom 'auth/login.html' template AND the SecureLoginForm with Captcha
    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html',
        authentication_form=SecureLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    
    # Registration & Support
    path('register/', core_views.register, name='register'),
    path('password-reset-info/', core_views.password_reset_contact, name='password_reset_contact'),

    # --- 3. INTERNAL ROUTING (The Brain) ---
    # This is the destination after login and for all dashboard links
    path('home/', core_views.home, name='home'),
    
    # Catch-all redirects for standard Django behaviors
    path('accounts/profile/', RedirectView.as_view(pattern_name='home')),
    path('accounts/login/', RedirectView.as_view(pattern_name='login')),
    path('dashboard/main/', RedirectView.as_view(pattern_name='home')),

    # --- 4. MODULAR APP ARCHITECTURE ---
    # Each module is isolated for better maintenance
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
    
    # Included Communication URLs
    path('communication/', include('communication.urls', namespace='communication')),
    
    # Required for the CAPTCHA images to render properly
    path('captcha/', include('captcha.urls')),
]