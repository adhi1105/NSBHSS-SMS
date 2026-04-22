from django.contrib import admin
from django.contrib import messages
from .models import Exam, Result, GradingScale

# --- ACTIONS (Bulk Operations) ---
@admin.action(description='🔒 LOCK Selected Exams (Prevent Teacher Edits)')
def lock_exams(modeladmin, request, queryset):
    queryset.update(is_locked=True, is_active=False)
    messages.success(request, "Selected exams have been LOCKED.")

@admin.action(description='📢 PUBLISH Results (Visible to Students)')
def publish_exams(modeladmin, request, queryset):
    queryset.update(is_published=True)
    messages.success(request, "Selected exams are now LIVE for students.")

# --- ADMIN VIEWS ---
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'is_active', 'is_locked', 'is_published')
    list_filter = ('is_locked', 'is_published', 'academic_session')
    actions = [lock_exams, publish_exams]

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'subject', 'marks_obtained', 'grade', 'is_passed')
    list_filter = ('exam', 'subject', 'is_passed')
    search_fields = ('student__user__first_name', 'student__student_id')
    readonly_fields = ('grade', 'grade_point', 'is_passed') # These are auto-calculated

@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = ('grade_name', 'min_percentage', 'max_percentage', 'grade_point')
    ordering = ('-min_percentage',)