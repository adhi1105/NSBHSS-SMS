from django.contrib import admin
from .models import FeeType, FeeStructure, Discount, StudentFee, Payment

@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('fee_type', 'class_room', 'amount', 'academic_year', 'due_date', 'late_fee_per_day')
    list_filter = ('academic_year', 'class_room', 'fee_type')
    search_fields = ('class_room__name', 'fee_type__name')
    list_editable = ('amount', 'due_date', 'late_fee_per_day')

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'description')

@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'structure', 'final_amount', 'paid_amount', 'balance', 'is_paid', 'due_date')
    list_filter = ('is_paid', 'structure__academic_year', 'structure__fee_type', 'structure__class_room')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__student_id')
    raw_id_fields = ('student', 'structure', 'discount')
    
    # CRITICAL: Lock down the calculated fields so they cannot be manually tampered with
    readonly_fields = ('original_amount', 'discount_amount', 'fine_amount', 'final_amount', 'paid_amount', 'balance', 'is_paid')

    fieldsets = (
        ('Assignment', {
            'fields': ('student', 'structure', 'due_date')
        }),
        ('Discounts & Fines', {
            'fields': ('discount', 'discount_amount', 'fine_amount')
        }),
        ('Accounting (Auto-Calculated)', {
            'fields': ('original_amount', 'final_amount', 'paid_amount', 'balance', 'is_paid')
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student_fee', 'amount', 'mode', 'date', 'transaction_id')
    list_filter = ('mode', 'date')
    search_fields = ('receipt_number', 'transaction_id', 'student_fee__student__user__first_name')
    raw_id_fields = ('student_fee',)
    readonly_fields = ('receipt_number',) # Auto-generated, should not be editable

    def get_readonly_fields(self, request, obj=None):
        if obj: # If editing an existing payment, lock the amount to prevent fraud
            return self.readonly_fields + ('amount', 'student_fee')
        return self.readonly_fields