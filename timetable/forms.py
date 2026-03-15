from django import forms
from .models import TimetableEntry  # Ensure this matches your model name

class TimetableForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = ['classroom', 'day', 'time_slot', 'subject', 'staff']
        
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'day': forms.Select(attrs={'class': 'form-select'}),
            'time_slot': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'staff': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(TimetableForm, self).__init__(*args, **kwargs)
        # Optional: Add "Select" placeholder to dropdowns
        for field in self.fields:
            self.fields[field].empty_label = "Select..."