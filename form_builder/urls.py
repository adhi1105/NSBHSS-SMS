from django.urls import path
from . import views

app_name = 'form_builder'

urlpatterns = [
    # Dashboard: List all forms
    path('', views.form_list, name='index'),
    
    # Create: Start a new form
    path('create/', views.create_form, name='create'),
    
    # Builder: Add fields to a form
    path('build/<int:form_id>/', views.form_builder, name='builder'),
    
    # Render: The public view for users to fill it out
    path('view/<int:form_id>/', views.render_form, name='render'),
    path('delete/<int:form_id>/', views.delete_form, name='delete_form'),
    path('analytics/<int:form_id>/', views.form_analytics, name='analytics'),
    path('export/<int:form_id>/', views.export_submissions, name='export'),
]