from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Stream, Subject

# --- 1. USER & PROFILE MANAGEMENT ---

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Role & Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        # Prevents crash when creating a new user before profile exists
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    
    def get_role(self, instance):
        if hasattr(instance, 'profile'):
            return instance.profile.role
        return '-'
    get_role.short_description = 'Role'

# Re-register User to include Profile inlines
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# --- 2. ACADEMIC STRUCTURE ---

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',) # REQUIRED for autocomplete in Timetable

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject_code', 'subject_type', 'is_practical')
    list_filter = ('subject_type', 'is_practical', 'streams')
    
    # CRITICAL: Enables search box for Timetable and other foreign keys
    search_fields = ('name', 'subject_code')
    
    # Provides a side-by-side UI for Science/Commerce stream selection
    filter_horizontal = ('streams',)