from django.contrib import admin
from .models import TimeSlot, TimetableEntry

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('period_number', 'start_time', 'end_time', 'is_break')
    list_editable = ('start_time', 'end_time', 'is_break') 
    ordering = ('period_number',)

@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'day', 'get_period', 'subject', 'staff')
    list_filter = ('day', 'classroom', 'staff')
    
    # This search box searches the TIMETABLE list
    search_fields = ('subject__name', 'staff__user__first_name', 'classroom__name')
    
    ordering = ('day', 'classroom', 'time_slot__period_number')
    
    # --- THE FIX ---
    # I have commented this out. To uncomment it, you must add 'search_fields' 
    # to SubjectAdmin, StaffAdmin, and ClassRoomAdmin in their respective apps.
    # autocomplete_fields = ['staff', 'subject', 'classroom'] 

    def get_period(self, obj):
        return f"P{obj.time_slot.period_number} ({obj.time_slot.start_time.strftime('%H:%M')})"
    get_period.short_description = 'Time Slot'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('classroom', 'subject', 'staff', 'time_slot')