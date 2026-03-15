# attendance/forms.py
from django import forms
from .models import AttendanceRecord

class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ('status', 'remarks')
        widgets = {
            # This changes the circle/box into a clean pill-shaped line
            'remarks': forms.TextInput(attrs={
                'class': 'form-control bg-light border-0 rounded-pill px-3',
                'placeholder': 'Add note (optional)...'
            }),
        }