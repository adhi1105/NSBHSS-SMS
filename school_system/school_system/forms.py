from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from captcha.fields import CaptchaField

# ==========================================
# 1. REGISTRATION FORM
# ==========================================
class UserRegisterForm(UserCreationForm):
    # Adding email, first name, and last name to the default Django registration
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Automatically apply the modern CSS classes to all fields so it matches our UI
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


# ==========================================
# 2. SECURE LOGIN FORM (WITH CAPTCHA)
# ==========================================
class SecureLoginForm(AuthenticationForm):
    # Add the Captcha field to the standard username/password login form
    captcha = CaptchaField(
        label="Security Check",
        error_messages={'invalid': 'Invalid CAPTCHA. Please try again.'}
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply the modern styling to match the login template
        self.fields['captcha'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Type the characters above'
        })
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})