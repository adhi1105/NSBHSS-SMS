from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import Course, Lesson, LessonVideo, StudyMaterial, Assignment

# --- 1. COURSE FORM ---
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'code', 'description', 'classroom', 'stream', 'subject', 'teacher', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Food Microbiology'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., FM-101'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'stream': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            if 'teacher' in self.fields:
                self.fields['teacher'].widget = forms.HiddenInput()
                self.fields['teacher'].required = False
        else:
            self.fields['teacher'].queryset = User.objects.filter(groups__name='Teacher')
            self.fields['teacher'].label = "Assigned Instructor"

# --- 2. LESSON FORM (Updated) ---
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        # Removed 'video_url' from here
        fields = ['title', 'content', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lesson Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Lesson content...'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1'}),
        }

# --- NEW: VIDEO FORMSET ---
# This factory creates a set of forms for LessonVideo attached to a Lesson
VideoFormSet = inlineformset_factory(
    Lesson,                 # Parent Model
    LessonVideo,            # Child Model
    fields=('title', 'youtube_url'), # Fields to show
    extra=1,                # Start with 1 empty row
    can_delete=True,        # Allow deleting existing videos
    widgets={
        'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Video Title (e.g. Part 1)'}),
        'youtube_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste YouTube URL here'}),
    }
)

# --- 3. STUDY MATERIAL FORM ---
class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['title', 'file_type', 'file_upload', 'external_link']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-select'}),
            'file_upload': forms.FileInput(attrs={'class': 'form-control'}),
            'external_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste URL here if selecting Video/Link'}),
        }

# --- 4. ASSIGNMENT FORM ---
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'total_marks', 'file_upload']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'file_upload': forms.FileInput(attrs={'class': 'form-control'}),
        }