from django.contrib import admin
from .models import Student
from attendance.models import AttendanceRecord
from fees.models import StudentFee

class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ('log', 'status', 'remarks')
    can_delete = False
    verbose_name = "Recent Attendance"
    verbose_name_plural = "Recent Attendance Records"

    def has_add_permission(self, request, obj=None):
        return False

class StudentFeeInline(admin.TabularInline):
    model = StudentFee
    extra = 0
    readonly_fields = ('structure', 'final_amount', 'paid_amount', 'balance', 'is_paid')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # This is the "magic" line that fixes the autocomplete requirement
    search_fields = ('student_id', 'user__first_name', 'user__last_name')
    # 1. list_display MUST include everything in list_editable
    list_display = (
        'student_id', 
        'get_full_name', 
        'classroom', 
        'roll_number',   # Added here because it is in list_editable
        'is_active',     # Added here because it is in list_editable
        'stream',
        'second_language'
    )
    
    # 2. These fields can be edited directly from the list
    list_editable = ('classroom', 'roll_number', 'is_active')
    
    # 3. Filters and Search
    list_filter = ('classroom', 'stream', 'second_language', 'is_active')
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'father_name')
    inlines = [AttendanceRecordInline, StudentFeeInline]
    
    # 4. Form Layout
    fieldsets = (
        ('Account Info', {
            'fields': ('user', 'student_id', 'is_active')
        }),
        ('Academic Details', {
            'fields': ('classroom', 'stream', 'first_language', 'second_language', 'roll_number', 'admission_date')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'gender', 'blood_group', 'photo')
        }),
        ('Guardian & Contact', {
            'fields': ('father_name', 'mother_name', 'emergency_phone', 'address')
        }),
    )
    
    readonly_fields = ('admission_date',)

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = "Student Name"