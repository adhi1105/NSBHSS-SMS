from django import forms
from .models import SubjectAllocation
from admission.models import ClassRoom

class AllocationForm(forms.ModelForm):
    class_room = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all().order_by('name'), # <--- Sorting Fix
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Target Class"
    )

    class Meta:
        model = SubjectAllocation
        fields = ['staff', 'subject', 'class_room', 'academic_year']
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'value': '2025-2026'}),
        }