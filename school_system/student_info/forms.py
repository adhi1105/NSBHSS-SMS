from django import forms
from django.contrib.auth.models import User
from admission.models import ClassRoom
from .models import Student
from school_system.models import Stream

class StudentEditForm(forms.ModelForm):
    # Manually added fields to update the linked User model
    first_name = forms.CharField(
        max_length=30, 
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3'})
    )
    last_name = forms.CharField(
        max_length=30, 
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3'})
    )

    class Meta:
        model = Student
        fields = [
            'classroom', 'roll_number', 'stream', 
            'first_language', 'second_language',
            'father_name', 'mother_name', 'emergency_phone', 'address', 
            'date_of_birth', 'gender', 'blood_group', 'is_active'
        ]
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'stream': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'first_language': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'second_language': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-3'}),
            'address': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3}),
            'father_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'roll_number': forms.NumberInput(attrs={'class': 'form-control rounded-3'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'gender': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill Names from User object for a smooth editing experience
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        student = super().save(commit=False)
        # Simultaneously update the related User model
        user = student.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        
        if commit:
            student.save()
        return student

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File",
        widget=forms.FileInput(attrs={'class': 'form-control rounded-pill'}),
        help_text="Expected format: First Name, Last Name, Email, Class Name, Parent Phone"
    )

    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Please upload a .csv file only.")
        return file

# --- SMOOTH FILTER FORM ---
class StudentFilterForm(forms.Form):
    search_query = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control border-0 shadow-none bg-transparent py-2', 
            'placeholder': 'Search name or ID...',
            'autocomplete': 'off'
        })
    )
    
    class_room = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all().order_by('standard', 'division'),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={
            'class': 'form-select border-0 shadow-none bg-transparent fw-bold text-dark small',
            'onchange': 'this.form.submit()' 
        })
    )
    
    stream = forms.ModelChoiceField(
        queryset=Stream.objects.all(),
        required=False,
        empty_label="All Streams",
        widget=forms.Select(attrs={
            'class': 'form-select border-0 shadow-none bg-transparent fw-bold text-dark small',
            'onchange': 'this.form.submit()'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Student.STUDENT_STATUS),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select border-0 shadow-none bg-transparent fw-bold text-dark small',
            'onchange': 'this.form.submit()'
        })
    )