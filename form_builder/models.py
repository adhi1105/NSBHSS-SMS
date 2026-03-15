from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ==========================================
# 1. THE FORM BLUEPRINT
# ==========================================
class CustomForm(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft (Staff Only)'),
        ('published', 'Published (Active)'),
        ('archived', 'Archived (Historical)'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # NEW: Categorization for better directory organization
    category = models.CharField(max_length=100, default="General", help_text="e.g., Admissions, Leave, Feedback")
    
    # NEW: Workflow Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # NEW: Response Limits
    limit_responses = models.PositiveIntegerField(default=0, help_text="Set to 0 for unlimited")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # NEW: Track edits
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# ==========================================
# 2. FIELD ARCHITECTURE
# ==========================================
class FormField(models.Model):
    FIELD_TYPES = [
        ('text', 'Short Text'),
        ('textarea', 'Long Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('email', 'Email'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('file', 'File Upload'), # NEW: File support for productivity
    ]

    custom_form = models.ForeignKey(CustomForm, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=200) 
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    help_text = models.CharField(max_length=200, blank=True)
    required = models.BooleanField(default=True)
    
    # NEW: Validation Logic
    placeholder = models.CharField(max_length=200, blank=True)
    
    choices = models.TextField(blank=True, help_text="Comma-separated options (for Dropdown/Checkbox)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    # --- THE FIX: Property to handle splitting logic in Python ---
    @property
    def get_choices(self):
        """
        Productivity Helper: Converts comma-separated string to a clean list.
        Prevents TemplateSyntaxError by avoiding 'split' filter in templates.
        """
        if self.choices:
            return [choice.strip() for choice in self.choices.split(',') if choice.strip()]
        return []

    # --- NEW: Integrity Check for choice formatting ---
    def clean(self):
        if self.field_type in ['select', 'checkbox'] and not self.choices:
            raise ValidationError({'choices': 'Choices are required for Dropdown or Checkbox fields.'})

    def __str__(self):
        return f"{self.custom_form.title} -> {self.label}"

# ==========================================
# 3. CONDITIONAL LOGIC ENGINE (PRODUCTIVITY)
# ==========================================

class LogicRule(models.Model):
    """
    Enables Smart Forms:
    Example: IF 'Stream' IS 'Science' -> SHOW 'Lab Electives'
    """
    ACTION_CHOICES = [('SHOW', 'Show'), ('HIDE', 'Hide')]
    OPERATOR_CHOICES = [('equals', 'Is Equal To'), ('not_equals', 'Is Not Equal To')]

    form = models.ForeignKey(CustomForm, on_delete=models.CASCADE, related_name='logic_rules')
    
    # The field that will be affected (e.g., 'Lab Electives')
    target_field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='affected_by')
    
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='SHOW')
    
    # The trigger (e.g., 'Stream')
    trigger_field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='triggers')
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES, default='equals')
    value = models.CharField(max_length=255, help_text="The answer value that triggers this rule")

    def __str__(self):
        return f"{self.action} {self.target_field.label} when {self.trigger_field.label} {self.operator} {self.value}"

# ==========================================
# 4. SUBMISSION REGISTRY
# ==========================================
class FormSubmission(models.Model):
    custom_form = models.ForeignKey(CustomForm, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # NEW: Review Tracking
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewer')
    
    data = models.JSONField() 

    def __str__(self):
        return f"Submission for {self.custom_form.title} by {self.submitted_by.username if self.submitted_by else 'Guest'}"