from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal  # <--- CRITICAL IMPORT ADDED
from student_info.models import Student
from admission.models import ClassRoom

# 1. FEE CATEGORIES
class FeeType(models.Model):
    name = models.CharField(max_length=100, unique=True) 
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

# 2. THE RULEBOOK
class FeeStructure(models.Model):
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    academic_year = models.CharField(max_length=20, default="2025-2026")
    due_date = models.DateField(null=True, blank=True)

    # --- PENALTY RULE ---
    late_fee_per_day = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00, 
        help_text="Fine amount per day after due date"
    )

    class Meta:
        unique_together = ['class_room', 'fee_type', 'academic_year']

    def __str__(self):
        return f"{self.class_room.name} - {self.fee_type.name}: {self.amount}"

# 3. DISCOUNT / SCHOLARSHIP RULES
class Discount(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

# 4. THE INVOICE
class StudentFee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    
    # Financials
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # FIX: Use 0 (int) instead of 0.00 (float) for default to avoid initial type errors
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    is_paid = models.BooleanField(default=False)
    due_date = models.DateField()

    # --- LOGIC TO CALCULATE FINE ---
    def update_fine(self):
        if self.is_paid:
            return 
            
        today = timezone.now().date()
        
        if self.due_date and today > self.due_date:
            overdue_days = (today - self.due_date).days
            
            # FIX: Convert days to Decimal before multiplying
            calculated_fine = Decimal(overdue_days) * self.structure.late_fee_per_day
            
            if calculated_fine != self.fine_amount:
                self.fine_amount = calculated_fine
                self.save() 
    
    def save(self, *args, **kwargs):
        # 1. Set Original Amount
        if not self.original_amount:
            self.original_amount = self.structure.amount
            
        # 2. Apply Discount (Safety: Convert 100 to Decimal)
        if self.discount:
            self.discount_amount = (self.original_amount * self.discount.percentage) / Decimal(100)
        else:
            self.discount_amount = Decimal(0)
        
        # 3. Calculate Final Amount (Safety: Explicitly convert fine_amount to Decimal)
        self.final_amount = (self.original_amount - self.discount_amount) + Decimal(self.fine_amount)
        
        # 4. Calculate Balance
        self.balance = self.final_amount - self.paid_amount
        
        # 5. Update Status
        if self.balance <= 0:
            self.is_paid = True
            self.balance = Decimal(0)
        else:
            self.is_paid = False
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.structure.fee_type.name}"

# 5. THE TRANSACTION
class Payment(models.Model):
    PAYMENT_MODES = [('Cash', 'Cash'), ('Online', 'Online'), ('Check', 'Check')]
    
    student_fee = models.ForeignKey(StudentFee, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    mode = models.CharField(max_length=10, choices=PAYMENT_MODES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCPT-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
        super().save(*args, **kwargs)
        
        # RECALCULATE Total Paid Amount to prevent duplication bugs
        total_paid = self.student_fee.payments.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        
        self.student_fee.paid_amount = total_paid
        self.student_fee.save()

    # --- THE SAFETY FIX: Handle Voided/Deleted Payments ---
    def delete(self, *args, **kwargs):
        """If a payment is voided/deleted, we must recalculate the fee balance."""
        fee = self.student_fee
        super().delete(*args, **kwargs) # Delete the payment first
        
        # Now recalculate the total without the deleted payment
        total_paid = fee.payments.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        fee.paid_amount = total_paid
        fee.save()

    def __str__(self):
        return f"Paid {self.amount} for {self.student_fee}"