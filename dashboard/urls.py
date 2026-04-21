from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # 1. CHANGE 'views.dashboard' TO 'views.home'
    path('', views.home, name='index'),

    # 2. Keep the API stats (This view still exists)
    path('api/dashboard-live/', views.live_dashboard_stats, name='live_dashboard_stats'),

    # 3. Keep the Profile view
    path('profile/', views.my_profile, name='my_profile'),

    # 4. Active Login Users view
    path('active-users/', views.active_login_users, name='active_users'),
]