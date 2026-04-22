from django import forms
from django.contrib.auth.models import User
from .models import Staff, SubjectAllocation

# Import ClassRoom from admission app for the assignment form
from admission.models import ClassRoom 

# --- 1. STAFF ONBOARDING FORM ---
class StaffOnboardingForm(forms.ModelForm):
    # User Fields (Virtual fields handled in save method)
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Staff
        fields = ['department', 'designation', 'qualification', 'joining_date', 'phone', 'is_teaching_staff']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_teaching_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        # 1. Create User instance
        user = User.objects.create_user(
            username=self.cleaned_data['email'].split('@')[0], # Simple username generation
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        # 2. Create Staff linked to User
        staff = super().save(commit=False)
        staff.user = user
        staff.employee_id = f"STF-{user.id:04d}" # Generate ID
        if commit:
            staff.save()
        return staff

# --- 2. SUBJECT ALLOCATION FORM ---
class AllocationForm(forms.ModelForm):
    class Meta:
        model = SubjectAllocation
        fields = ['staff', 'subject', 'classroom']
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'classroom': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(AllocationForm, self).__init__(*args, **kwargs)
        # Optional: Filter staff dropdown to only show teaching staff
        self.fields['staff'].queryset = Staff.objects.filter(is_teaching_staff=True)

# --- 3. ASSIGN CLASS TEACHER FORM (New) ---
class AssignClassTeacherForm(forms.Form):
    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all().order_by('standard', 'division'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Class"
    )
    
    staff = forms.ModelChoiceField(
        # Filter: Only show active teaching staff
        queryset=Staff.objects.filter(is_teaching_staff=True, status='Active'), 
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Teacher",
        empty_label="-- Choose Teacher --"
    )

    def clean_staff(self):
        return self.cleaned_data['staff']