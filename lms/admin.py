from django.contrib import admin
from .models import Course, Lesson, StudyMaterial, Assignment
# Remove 'Stream' from the import if you aren't using it for something else here
from school_system.models import Stream 

# --- REMOVED: admin.site.register(Stream) ---
# This was causing the AlreadyRegistered error because it is already 
# registered in school_system/admin.py

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1

class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    # Added 'stream' to the list display for better organization
    list_display = ('title', 'code', 'stream', 'classroom', 'teacher')
    list_filter = ('stream', 'classroom') # Added filters sidebar

admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson)
admin.site.register(StudyMaterial)
admin.site.register(Assignment)