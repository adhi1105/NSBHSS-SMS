from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.library_home, name='index'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('add-book/', views.add_book, name='add_book'),
    
    # --- THIS IS THE MISSING LINE CAUSING THE ERROR ---
    path('issue-book/', views.issue_book, name='issue_book'),
    # --------------------------------------------------
    path('catalog/', views.book_catalog, name='book_catalog'),
    path('edit-book/<int:book_id>/', views.edit_book, name='edit_book'),

    path('request/issue/<int:book_id>/', views.request_issue, name='request_issue'),
    path('request/return/<int:record_id>/', views.request_return, name='request_return'),
    path('approve/<int:record_id>/', views.approve_request, name='approve_request'),
]