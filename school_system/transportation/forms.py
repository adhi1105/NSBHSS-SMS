from django import forms
from .models import Vehicle, Route

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_no', 'model_name', 'capacity', 'driver', 'insurance_expiry', 'pollution_expiry', 'is_active']
        widgets = {
            'vehicle_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'KL-01-AB-1234'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tata Starbus'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'insurance_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pollution_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['name', 'vehicle', 'start_point', 'end_point']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Route 1 - City Center'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'start_point': forms.TextInput(attrs={'class': 'form-control'}),
            'end_point': forms.TextInput(attrs={'class': 'form-control'}),
        }