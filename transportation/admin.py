from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, Driver, Route, Stop, TransportSubscription

# --- INLINE: Add Stops directly inside Route ---
class StopInline(admin.TabularInline):
    model = Stop
    extra = 1

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle', 'start_point', 'end_point')
    inlines = [StopInline]

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_no', 'model_name', 'driver', 'capacity', 'maintenance_status')
    list_filter = ('is_active',)
    
    # Color-coded Maintenance Alert
    def maintenance_status(self, obj):
        if obj.needs_maintenance():
            return format_html('<span style="color:red; font-weight:bold;">⚠️ Renewal Due</span>')
        return format_html('<span style="color:green;">✅ OK</span>')

@admin.register(TransportSubscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'route', 'stop', 'monthly_fee_display', 'is_active')
    list_filter = ('route', 'is_active')
    search_fields = ('student__user__first_name', 'student__student_id')

    def monthly_fee_display(self, obj):
        return obj.stop.monthly_fee if obj.stop else "0.00"
    monthly_fee_display.short_description = "Fee Amount"