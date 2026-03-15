from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta

# --- IDENTITY INTEGRATION ---
from staff.decorators import allowed_users

# --- MODELS & FORMS ---
from .models import Book, BorrowRecord, Category
from .forms import BookForm, IssueBookForm  
from student_info.models import Student
from staff.models import Staff

# --- 1. TRAFFIC CONTROLLER ---
@login_required
def library_home(request):
    """
    Identity-Aware Traffic Controller.
    Redirects to appropriate terminal based on security clearance.
    """
    user_group = None
    if request.user.groups.exists():
        user_group = request.user.groups.all()[0].name

    if request.user.is_superuser or user_group in ['Admin', 'Librarian']:
        return redirect('library:admin_dashboard')
    else:
        return redirect('library:user_dashboard')

# --- 2. LIBRARIAN DASHBOARD (Operational Control) ---
@login_required
@allowed_users(allowed_roles=['Librarian', 'Admin'])
def admin_dashboard(request):
    # 1. Real-time Telemetry
    total_books = Book.objects.count()
    issued_books = BorrowRecord.objects.filter(status='Issued').count()
    
    # 2. Circulation Queue (Pending Registry Actions)
    pending_list = BorrowRecord.objects.filter(
        status__in=['Requested', 'Return Requested']
    ).select_related('book', 'student__user', 'staff__user').order_by('issue_date')
    
    pending_count = pending_list.count()

    # 3. Fine/Overdue Matrix
    issued_records = BorrowRecord.objects.filter(status='Issued')
    overdue_list = [r for r in issued_records if r.current_fine > 0]

    context = {
        'total_books': total_books,
        'issued_books': issued_books,
        'pending_requests': pending_count,
        'pending_list': pending_list,
        'overdue_list': overdue_list,
    }
    return render(request, 'library/admin_dashboard.html', context)

# --- 3. USER DASHBOARD (Student/Teacher Portal) ---
@login_required
def user_dashboard(request):
    # 1. Resolve Identity Profile
    student_profile = Student.objects.filter(user=request.user).first()
    staff_profile = Staff.objects.filter(user=request.user).first()
    
    # 2. Personal Borrowing History
    my_records = []
    if student_profile:
        my_records = BorrowRecord.objects.filter(student=student_profile).select_related('book').order_by('-issue_date')
    elif staff_profile:
        my_records = BorrowRecord.objects.filter(staff=staff_profile).select_related('book').order_by('-issue_date')

    # 3. Catalog Search Logic
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    books = Book.objects.all().select_related('category')
    
    if query:
        books = books.filter(
            Q(title__icontains=query) | 
            Q(author__icontains=query) | 
            Q(category__name__icontains=query)
        )
    if category_id:
        books = books.filter(category_id=category_id)

    return render(request, 'library/user_dashboard.html', {
        'my_records': my_records,
        'books': books,
        'categories': Category.objects.all(),
        'search_query': query
    })

# --- 4. ACTION: ADD BOOK (Clearance Required) ---
@login_required
@allowed_users(allowed_roles=['Librarian', 'Admin'])
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "ASSET_CREATED: New book added to catalog.")
            return redirect('library:admin_dashboard')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Register New Asset'})

# --- 5. ACTION: REQUEST ISSUE (Standard Node) ---
@login_required
def request_issue(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if book.available_copies < 1:
        messages.error(request, "RESOURCE_UNAVAILABLE: Out of stock.")
        return redirect('library:user_dashboard')

    student = Student.objects.filter(user=request.user).first()
    staff = Staff.objects.filter(user=request.user).first()

    if not student and not staff:
        messages.error(request, "IDENTITY_ERROR: Unauthorized node type.")
        return redirect('home')

    existing = BorrowRecord.objects.filter(
        book=book, 
        status__in=['Requested', 'Issued'],
        student=student, 
        staff=staff
    ).exists()
    
    if existing:
        messages.warning(request, "DUPLICATE_REQUEST: Process already active for this asset.")
        return redirect('library:user_dashboard')

    BorrowRecord.objects.create(
        book=book,
        student=student,
        staff=staff,
        status='Requested',
        issue_date=timezone.now().date()
    )
    
    book.available_copies -= 1
    book.save()
    
    messages.success(request, "REQUEST_QUEUED: Awaiting Librarian approval.")
    return redirect('library:user_dashboard')

# --- 6. ACTION: REQUEST RETURN (Standard Node) ---
@login_required
def request_return(request, record_id):
    record = get_object_or_404(BorrowRecord, id=record_id)
    
    # Ownership Validation
    user_is_owner = False
    if record.student and record.student.user == request.user: user_is_owner = True
    if record.staff and record.staff.user == request.user: user_is_owner = True
    
    if not user_is_owner:
        messages.error(request, "PERMISSION_DENIED: Critical violation.")
        return redirect('library:user_dashboard')

    if record.status == 'Issued':
        record.status = 'Return Requested'
        record.save()
        messages.success(request, "RETURN_PENDING: Asset awaiting drop-off.")
    
    return redirect('library:user_dashboard')

# --- 7. ACTION: APPROVE REQUEST (Librarian/Admin Only) ---
@login_required
@allowed_users(allowed_roles=['Librarian', 'Admin'])
def approve_request(request, record_id):
    record = get_object_or_404(BorrowRecord, id=record_id)
    
    if record.status == 'Requested':
        record.status = 'Issued'
        record.save() 
        messages.success(request, f"TRANSACTION_COMPLETE: Asset issued to {record.borrower_name}.")
        
    elif record.status == 'Return Requested':
        record.status = 'Returned'
        record.save()
        
        if record.fine_amount > 0:
            messages.warning(request, f"ASSET_RETURNED: PENALTY_DUE ₹{record.fine_amount}")
        else:
            messages.success(request, "ASSET_RETURNED: Record cleared.")
            
    return redirect('library:admin_dashboard')

# --- 8. ACTION: MANUAL ISSUE (Librarian Only) ---
@login_required
@allowed_users(allowed_roles=['Librarian', 'Admin'])
def issue_book(request):
    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            book = form.cleaned_data['book']
            student = form.cleaned_data['student']
            staff = form.cleaned_data['staff']
            
            if book.available_copies < 1:
                messages.error(request, f"RESOURCE_UNAVAILABLE: '{book.title}' out of stock.")
                return redirect('library:issue_book')
            
            BorrowRecord.objects.create(
                book=book,
                student=student,
                staff=staff,
                status='Issued',
                issue_date=timezone.now().date()
            )
            
            book.available_copies -= 1
            book.save()
            
            messages.success(request, f"MANUAL_ISSUE_COMPLETE: Processed for {student or staff}.")
            return redirect('library:admin_dashboard')
    else:
        form = IssueBookForm()

    return render(request, 'library/issue_book.html', {'form': form})

# --- 9. CATALOG: SHARED REGISTRY VIEW ---
@login_required
def book_catalog(request):
    query = request.GET.get('q')
    books = Book.objects.all().select_related('category').order_by('title')
    
    if query:
        books = books.filter(
            Q(title__icontains=query) | 
            Q(author__icontains=query) | 
            Q(category__name__icontains=query)
        )

    # Resolve Librarian Role for Template
    is_lib_node = False
    if request.user.groups.filter(name__in=['Admin', 'Librarian']).exists():
        is_lib_node = True

    context = {
        'books': books,
        'is_librarian': is_lib_node,
        'search_query': query
    }
    return render(request, 'library/book_catalog.html', context)

# --- 10. ACTION: EDIT BOOK (Clearance Required) ---
@login_required
@allowed_users(allowed_roles=['Librarian', 'Admin'])
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f"METADATA_UPDATED: '{book.title}' synced successfully.")
            return redirect('library:book_catalog')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'library/book_form.html', {
        'form': form, 
        'title': 'Modify Asset Metadata'
    })