from django.contrib import admin
from .models import ClassRoom, AdmissionApplication, AdmissionDocument

# 1. Register ClassRoom
@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    # We use 'get_available_seats' (the function below) instead of 'available_seats'
    list_display = ('name', 'standard', 'division', 'stream', 'occupied_seats', 'total_seats', 'get_available_seats')
    list_filter = ('standard', 'stream')
    search_fields = ('name',)
    readonly_fields = ('occupied_seats',)

    # FIX: Define the calculation explicitly for the Admin Panel
    @admin.display(description='Available Seats')
    def get_available_seats(self, obj):
        return obj.total_seats - obj.occupied_seats

# 2. Document Inline
class DocumentInline(admin.TabularInline):
    model = AdmissionDocument
    extra = 0

# 3. Register Applications
@admin.register(AdmissionApplication)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'class_applied', 'parent_name', 'status', 'applied_date')
    list_filter = ('status', 'class_applied')
    search_fields = ('student_name', 'parent_name', 'phone')
    inlines = [DocumentInline]
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        queryset.update(status='Approved')
    approve_selected.short_description = "Mark selected as Approved"

    def reject_selected(self, request, queryset):
        queryset.update(status='Rejected')
    reject_selected.short_description = "Mark selected as Rejected"

# 4. Register Documents
admin.site.register(AdmissionDocument)