from django.db import models
from django.utils import timezone
from student_info.models import Student
from staff.models import Staff
from datetime import timedelta, date

# --- CATEGORIES ---
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    class Meta:
        verbose_name_plural = "Categories"
    def __str__(self):
        return self.name

# --- BOOK CATALOG ---
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    
    # Inventory & Location
    shelf_location = models.CharField(max_length=50, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    
    # Digital Link
    pdf_file = models.FileField(upload_to='ebooks/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- CIRCULATION RECORD ---
class BorrowRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True)
    
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('Requested', 'Requested (Pending Approval)'),
        ('Issued', 'Issued (Currently Borrowed)'),
        ('Return Requested', 'Return Requested'),
        ('Returned', 'Returned (Completed)'),
        ('Lost', 'Lost'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Requested')
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    @property
    def borrower_name(self):
        if self.student: return f"{self.student.user.get_full_name()} (Student)"
        if self.staff: return f"{self.staff.user.get_full_name()} (Staff)"
        return "Unknown"

    @property
    def current_fine(self):
        if self.status in ['Issued', 'Return Requested'] and self.due_date:
            if date.today() > self.due_date:
                overdue_days = (date.today() - self.due_date).days
                return overdue_days * 10.0 
        return self.fine_amount 

    # --- THE SAFE SAVE METHOD ---
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        # Look up the old status before we save changes
        if not is_new:
            old_status = BorrowRecord.objects.get(pk=self.pk).status

        # Transition from anything to ISSUED
        if self.status == 'Issued' and old_status != 'Issued':
            # Set due date
            if not self.due_date:
                days = 30 if self.staff else 14
                self.due_date = timezone.now().date() + timedelta(days=days)
            
            # Safely decrease inventory
            if self.book.available_copies > 0:
                self.book.available_copies -= 1
                self.book.save()

        # Transition from anything to RETURNED
        if self.status == 'Returned' and old_status != 'Returned':
            # Set return date & calculate fine
            if not self.return_date:
                self.return_date = timezone.now().date()
            if self.return_date > self.due_date:
                overdue_days = (self.return_date - self.due_date).days
                self.fine_amount = overdue_days * 10.0
            
            # Safely restock inventory
            self.book.available_copies += 1
            self.book.save()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} - {self.status}"