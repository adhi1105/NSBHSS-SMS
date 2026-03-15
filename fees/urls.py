from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    # 1. The Smart Entry Point (Traffic Controller)
    path('', views.index, name='index'),
    
    # 2. NEW: Admin Dashboard (The missing link)
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # 3. Admin Tools
    path('generate/', views.invoice_generator, name='invoice_generator'),
    path('create-rule/', views.create_fee_rule, name='create_fee_rule'),

    # 4. Cashier / Staff Tools
    path('cashier/', views.cashier_search, name='cashier_search'),
    path('cashier/student/<int:student_id>/', views.student_invoices, name='student_invoices'),
    path('pay/<int:fee_id>/', views.record_payment, name='record_payment'),
    
    # 5. Student Tools
    path('student/pay/<int:fee_id>/', views.student_pay_online, name='student_pay_online'),
]