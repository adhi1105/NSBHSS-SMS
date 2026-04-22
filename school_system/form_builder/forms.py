from django import forms
from .models import CustomForm, FormField, LogicRule, FormSubmission

# ==========================================
# 1. CORE FORM CONFIGURATION
# ==========================================
class CreateFormForm(forms.ModelForm):
    class Meta:
        model = CustomForm
        fields = ['title', 'category', 'status', 'description', 'limit_responses']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Science Fair Registration'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Admissions, Feedback, Sports'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Enter a brief description of what this form is for.'
            }),
            'limit_responses': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0 for unlimited'
            }),
        }

# ==========================================
# 2. FIELD DESIGNER
# ==========================================
class AddFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = ['label', 'field_type', 'required', 'placeholder', 'choices', 'order']
        widgets = {
            'label': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. What is your age?'
            }),
            'field_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'placeholder': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ghost text inside input'
            }),
            'choices': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Option 1, Option 2, Option 3 (Only for Dropdowns/Checkboxes)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }

# ==========================================
# 3. CONDITIONAL LOGIC ENGINE (NEW)
# ==========================================

class AddLogicRuleForm(forms.ModelForm):
    """
    Form to define smart behavior: 
    'If Field A equals X, then SHOW Field B'
    """
    class Meta:
        model = LogicRule
        fields = ['target_field', 'action', 'trigger_field', 'operator', 'value']
        widgets = {
            'target_field': forms.Select(attrs={'class': 'form-select'}),
            'action': forms.Select(attrs={'class': 'form-select'}),
            'trigger_field': forms.Select(attrs={'class': 'form-select'}),
            'operator': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Value to match'
            }),
        }

    def __init__(self, *args, **kwargs):
        # We limit the dropdowns to fields belonging only to the current form
        form_instance = kwargs.pop('form_instance', None)
        super().__init__(*args, **kwargs)
        if form_instance:
            self.fields['target_field'].queryset = FormField.objects.filter(custom_form=form_instance)
            self.fields['trigger_field'].queryset = FormField.objects.filter(custom_form=form_instance)

# ==========================================
# 4. SUBMISSION PROCESSING (NEW)
# ==========================================
class SubmissionReviewForm(forms.ModelForm):
    """ Used by staff to mark a submission as processed/reviewed """
    class Meta:
        model = FormSubmission
        fields = ['is_reviewed']
        widgets = {
            'is_reviewed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }