from django import forms
from .models import AdmissionApplication, AdmissionDocument, ClassRoom
from school_system.models import Subject

# --- STUDENT APPLICATION FORM (Only Admission Logic Remains) ---
class ApplicationForm(forms.ModelForm):
    class Meta:
        model = AdmissionApplication
        fields = [
            'student_name', 'date_of_birth', 'gender', 
            'class_applied', 'stream_applied', 
            'first_language', 'second_language', 
            'optional_subject',
            'parent_name', 'phone', 'email', 'address',
            # Document Fields
            'passport_photo', 'id_proof', 'previous_mark_sheet', 'transfer_certificate'
        ]
        
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'class_applied': forms.Select(attrs={'class': 'form-select'}),
            'stream_applied': forms.Select(attrs={'class': 'form-select'}),
            'first_language': forms.Select(attrs={'class': 'form-select'}),
            'second_language': forms.Select(attrs={'class': 'form-select'}),
            'optional_subject': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),

            # File Widgets
            'passport_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'id_proof': forms.FileInput(attrs={'class': 'form-control'}),
            'previous_mark_sheet': forms.FileInput(attrs={'class': 'form-control'}),
            'transfer_certificate': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        
        # 1. Filter Classes (11 & 12 only)
        self.fields['class_applied'].queryset = ClassRoom.objects.filter(
            standard__in=['11', '12']
        ).order_by('standard', 'division')
        
        # 2. First Language: English Default
        self.fields['first_language'].queryset = Subject.objects.filter(name='English')
        try:
            english = Subject.objects.get(name='English')
            self.fields['first_language'].initial = english
        except Subject.DoesNotExist:
            pass

        # 3. Second Language (Specific List)
        self.fields['second_language'].queryset = Subject.objects.filter(
            name__in=['Hindi', 'Malayalam', 'Arabic', 'Sanskrit', 'French'],
            subject_type='Language'
        )

        # 4. Optional Subject (Electives Only)
        self.fields['optional_subject'].queryset = Subject.objects.filter(
            subject_type='Elective'
        )