from django import forms
from django.core.exceptions import ValidationError
from .models import Book, BorrowRecord
from student_info.models import Student
from staff.models import Staff

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'shelf_location': forms.TextInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class IssueBookForm(forms.ModelForm):
    # Filter: Only show books that have copies available
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Make these optional in the form definition so we can validate them manually
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    staff = forms.ModelChoiceField(
        queryset=Staff.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    due_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="Leave blank for auto-calculation (14 days for Students, 30 for Staff)"
    )

    class Meta:
        model = BorrowRecord
        fields = ['book', 'student', 'staff', 'due_date']

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        staff = cleaned_data.get('staff')

        # Rule: Must select exactly one borrower
        if not student and not staff:
            raise ValidationError("You must select either a Student OR a Staff member.")
        if student and staff:
            raise ValidationError("Please select only one borrower (Student OR Staff), not both.")
        
        return cleaned_data