from django.urls import path
from . import views

app_name = 'transportation'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Create
    path('vehicle/add/', views.create_vehicle, name='create_vehicle'),
    path('route/add/', views.create_route, name='create_route'),
    
    # Edit (NEW)
    path('vehicle/edit/<int:pk>/', views.edit_vehicle, name='edit_vehicle'),
    path('route/edit/<int:pk>/', views.edit_route, name='edit_route'),
]