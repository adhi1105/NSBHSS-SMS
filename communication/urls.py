from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('whatsapp/', views.bulk_whatsapp_view, name='bulk_whatsapp'),
    path('whatsapp/settings/', views.api_settings_view, name='api_settings'),
    path('whatsapp/api/fetch-recipients/', views.api_filter_users, name='api_filter_users'),
    path('whatsapp/api/pair/', views.whatsapp_pairing_view, name='whatsapp_pairing'),
]
