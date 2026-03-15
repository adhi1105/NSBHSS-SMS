from django.contrib import admin
from .models import AttendanceLog, AttendanceRecord

class AttendanceRecordInline(admin.TabularInline):
    """Allows editing student records directly inside the Session page"""
    model = AttendanceRecord
    extra = 0  
    can_delete = True
    fields = ('student', 'status', 'remarks')
    autocomplete_fields = ['student'] 

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    # Note: 'taken_by' must exist in your AttendanceLog model
    list_display = ('classroom', 'subject', 'date', 'get_record_count')
    inlines = [AttendanceRecordInline]

    def get_record_count(self, obj):
        return obj.records.count()
    get_record_count.short_description = 'Total Students'

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    # We use custom method names here instead of direct field names
    list_display = ('student', 'status', 'get_classroom', 'get_subject', 'get_date')
    list_filter = ('status', 'log__classroom', 'log__date')
    search_fields = ('student__user__first_name', 'student__student_id')

    # 1. Get Classroom from the parent Log
    def get_classroom(self, obj):
        return obj.log.classroom if obj.log else "-"
    get_classroom.short_description = 'Classroom'

    # 2. Get Subject from the parent Log
    def get_subject(self, obj):
        return obj.log.subject if obj.log else "-"
    get_subject.short_description = 'Subject'

    # 3. Get Date from the parent Log
    def get_date(self, obj):
        return obj.log.date if obj.log else "-"
    get_date.short_description = 'Date'