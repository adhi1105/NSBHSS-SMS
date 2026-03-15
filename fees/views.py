from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone  
from student_info.models import Student
from .models import FeeStructure, StudentFee, Payment
from .forms import InvoiceGeneratorForm, PaymentForm, FeeStructureForm

# --- IDENTITY INTEGRATION: IMPORT THE SECURITY LOCK ---
from staff.decorators import allowed_users

# --- 1. DASHBOARD / TRAFFIC CONTROLLER ---
@login_required
def index(request):
    """
    Main Fee Portal Entry Point.
    Morphes based on the Identity Node accessing it.
    """
    # 1. Access Check: Identify User Group
    user_group = None
    if request.user.groups.exists():
        user_group = request.user.groups.all()[0].name

    # 2. Redirect Staff Nodes to their specific terminals
    if request.user.is_superuser or user_group in ['Admin', 'Cashier', 'Dept_Admin', 'Office_Staff']:
        if request.user.is_superuser or user_group == 'Admin':
            return redirect('fees:admin_dashboard')
        return redirect('fees:cashier_search')
    
    # 3. Student Dashboard Logic (Standard Registry)
    try:
        student = Student.objects.get(user=request.user)
        
        invoices = StudentFee.objects.filter(student=student).select_related(
            'structure__fee_type', 
            'structure__class_room'
        ).order_by('is_paid', 'due_date')

        # TRIGGER FINE CALCULATION
        for invoice in invoices:
            invoice.update_fine()

        transactions = Payment.objects.filter(
            student_fee__student=student
        ).select_related('student_fee__structure__fee_type').order_by('-date')

        total_payable = invoices.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
        total_paid = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        total_balance = invoices.aggregate(Sum('balance'))['balance__sum'] or 0

        context = {
            'student': student,
            'invoices': invoices,
            'transactions': transactions,
            'summary': {
                'payable': total_payable,
                'paid': total_paid,
                'balance': total_balance
            }
        }
        return render(request, 'fees/student_index.html', context)
        
    except Student.DoesNotExist:
        return render(request, 'error.html', {
            'message': "Finance Profile Not Found. Contact system admin to verify student link."
        })

# --- 2. ADMIN FLEXIBLE DASHBOARD ---
@login_required
@allowed_users(allowed_roles=['Admin'])
def admin_dashboard(request):
    today = timezone.now().date()
    
    # A. KEY METRICS
    total_collected = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expected = StudentFee.objects.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
    total_pending = StudentFee.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    todays_collection = Payment.objects.filter(date__date=today).aggregate(Sum('amount'))['amount__sum'] or 0

    # B. DEFAULTERS LIST
    defaulters = StudentFee.objects.filter(
        balance__gt=0, 
        due_date__lt=today
    ).select_related('student', 'structure').order_by('due_date')[:10]

    # C. RECENT TRANSACTIONS
    recent_payments = Payment.objects.select_related('student_fee__student').order_by('-date')[:5]

    # D. ACTIVE FEE STRUCTURES
    fee_rules = FeeStructure.objects.select_related('class_room', 'fee_type').all()

    context = {
        'stats': {
            'collected': total_collected,
            'pending': total_pending,
            'today': todays_collection,
            'expected': total_expected
        },
        'defaulters': defaulters,
        'recent_payments': recent_payments,
        'fee_rules': fee_rules,
    }
    return render(request, 'fees/admin_dashboard.html', context)

# --- 3. INVOICE GENERATOR ---
@login_required
@allowed_users(allowed_roles=['Admin', 'Office_Staff'])
def invoice_generator(request):
    if request.method == 'POST':
        form = InvoiceGeneratorForm(request.POST)
        if form.is_valid():
            structure = form.cleaned_data['fee_structure']
            due_date = form.cleaned_data['due_date']
            
            target_class = structure.class_room
            students = Student.objects.filter(classroom=target_class) 
            
            if not students.exists():
                messages.warning(request, f"No active students found in {target_class.name}!")
                return redirect('fees:invoice_generator')

            count = 0
            for student in students:
                obj, created = StudentFee.objects.get_or_create(
                    student=student,
                    structure=structure,
                    defaults={
                        'original_amount': structure.amount,
                        'final_amount': structure.amount,
                        'balance': structure.amount,
                        'due_date': due_date
                    }
                )
                if created: count += 1
            
            if count > 0:
                messages.success(request, f"Generated {count} invoices for {target_class.name}.")
            else:
                messages.info(request, "Invoices already exist for this class.")
            return redirect('fees:invoice_generator')
    else:
        form = InvoiceGeneratorForm()

    return render(request, 'fees/invoice_generator.html', {'form': form})

# --- 4. CREATE RULE ---
@login_required
@allowed_users(allowed_roles=['Admin'])
def create_fee_rule(request):
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            try:
                rule = form.save()
                messages.success(request, f"Identity Rule Created: {rule}")
                return redirect('fees:admin_dashboard') 
            except Exception as e:
                messages.error(request, f"Protocol Error: {str(e)}")
        else:
            messages.error(request, "Validation Failed. Check inputs.")
    else:
        form = FeeStructureForm()
    
    return render(request, 'fees/create_rule.html', {'form': form})

# --- 5. CASHIER: SEARCH TERMINAL ---
@login_required
@allowed_users(allowed_roles=['Cashier', 'Admin', 'Office_Staff'])
def cashier_search(request):
    query = request.GET.get('q')
    students = None
    if query:
        students = Student.objects.filter(
            user__first_name__icontains=query
        ) | Student.objects.filter(
            student_id__icontains=query
        )
    return render(request, 'fees/cashier_search.html', {'students': students, 'query': query})

# --- 6. CASHIER: STUDENT INVOICE LIST ---
@login_required
@allowed_users(allowed_roles=['Cashier', 'Admin'])
def student_invoices(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    fees = StudentFee.objects.filter(student=student).order_by('is_paid', 'due_date')
    
    for fee in fees:
        fee.update_fine()
    
    return render(request, 'fees/cashier_student_list.html', {
        'student': student,
        'fees': fees
    })

# --- 7. CASHIER: RECORD PAYMENT (THE NUCLEAR LOCK) ---
@login_required
@allowed_users(allowed_roles=['Cashier', 'Admin'])
def record_payment(request, fee_id):
    invoice = get_object_or_404(StudentFee, id=fee_id)
    invoice.update_fine()
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.student_fee = invoice
            
            if payment.amount > invoice.balance:
                messages.error(request, f"Overflow Error: Payment exceeds balance.")
                return redirect('fees:record_payment', fee_id=fee_id)
                
            payment.save()
            messages.success(request, f"Transaction Complete: ₹{payment.amount} recorded.")
            return redirect('fees:student_invoices', student_id=invoice.student.id)
    else:
        form = PaymentForm(initial={'amount': invoice.balance})

    return render(request, 'fees/record_payment.html', {'invoice': invoice, 'form': form})

# --- 8. STUDENT: PAY ONLINE ---
@login_required
def student_pay_online(request, fee_id):
    invoice = get_object_or_404(StudentFee, id=fee_id, student__user=request.user)
    invoice.update_fine()

    if request.method == 'POST':
        amount_to_pay = invoice.balance
        
        Payment.objects.create(
            student_fee=invoice,
            amount=amount_to_pay,
            mode='Online',
            transaction_id=f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            remarks="Digital Ledger Payment"
        )
        
        # Balance is automatically handled by the Payment model's save method usually, 
        # but manually updating here if your model doesn't have a signal.
        invoice.paid_amount += amount_to_pay
        invoice.save()
        
        messages.success(request, f"Digital Transaction Successful! ₹{amount_to_pay} cleared.")
        return redirect('fees:index')

    return render(request, 'fees/student_payment_confirm.html', {'invoice': invoice})