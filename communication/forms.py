from django import forms
from .models import CommunicationSettings

class CommunicationSettingsForm(forms.ModelForm):
    class Meta:
        model = CommunicationSettings
        fields = ['provider', 'api_key', 'account_sid', 'sender_number']
        widgets = {
            'provider': forms.Select(attrs={'class': 'form-select bg-sage bg-opacity-50 border-0 rounded-3 py-2'}),
            'api_key': forms.PasswordInput(render_value=True, attrs={
                'class': 'form-control bg-sage bg-opacity-50 border-0 rounded-3 py-2',
                'placeholder': 'Enter Ultramsg Token, Twilio Auth, or Meta Bearer'
            }),
            'account_sid': forms.TextInput(attrs={
                'class': 'form-control bg-sage bg-opacity-50 border-0 rounded-3 py-2',
                'placeholder': 'Ultramsg Instance ID or Twilio Account SID'
            }),
            'sender_number': forms.TextInput(attrs={
                'class': 'form-control bg-sage bg-opacity-50 border-0 rounded-3 py-2',
                'placeholder': '+123456789 (Twilio/Meta only)'
            })
        }
