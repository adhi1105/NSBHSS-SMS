from django import forms
from .models import FeeStructure, Payment

# --- 1. RULE CREATION FORM (ADMIN) ---
class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        # Added 'late_fee_per_day' to the fields list
        fields = ['class_room', 'fee_type', 'amount', 'late_fee_per_day', 'due_date', 'academic_year']
        widgets = {
            'class_room': forms.Select(attrs={'class': 'form-select'}),
            'fee_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            
            # New Widget for Late Fee
            'late_fee_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10.00'}),
            
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'value': '2025-2026'}),
        }
        labels = {
            'class_room': 'Target Class',
            'fee_type': 'Fee Category',
            'late_fee_per_day': 'Fine Per Day (₹)',
        }

# --- 2. INVOICE GENERATOR FORM (ADMIN) ---
class InvoiceGeneratorForm(forms.Form):
    fee_structure = forms.ModelChoiceField(
        queryset=FeeStructure.objects.select_related('class_room', 'fee_type').all(),
        label="Select Fee Rule",
        widget=forms.Select(attrs={'class': 'form-select form-select-lg fw-bold'}),
        help_text="Choose the Class and Fee Type (e.g., Class 10 - Tuition)"
    )
    
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Payment Due Date"
    )

# --- 3. PAYMENT ENTRY FORM (CASHIER) ---
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'mode', 'transaction_id', 'remarks']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-lg fw-bold', 'placeholder': '0.00'}),
            'mode': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cheque No. / UPI Ref / Bank ID'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional transaction notes...'}),
        }