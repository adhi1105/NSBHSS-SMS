from django.contrib import admin, messages
from django.contrib.auth.models import User, Group
from django.db import transaction
from .models import Staff, Department, SubjectAllocation

# --- 1. ACTION: Reset Password Function ---
@admin.action(description='Reset password to "Staff123"')
def reset_password_to_default(modeladmin, request, queryset):
    updated_count = 0
    for staff in queryset:
        if staff.user:
            staff.user.set_password("Staff123")
            staff.user.save()
            updated_count += 1
    
    modeladmin.message_user(request, f"Reset {updated_count} passwords.", messages.SUCCESS)

# --- 2. ACTION: The Absolute Override Fix ---
@admin.action(description='FIX ALL ROLES: Absolute Override to Teacher')
def move_to_teacher_role(modeladmin, request, queryset):
    teacher_group, _ = Group.objects.get_or_create(name='Teacher')
    updated_count = 0
    
    with transaction.atomic():
        for staff in queryset:
            if staff.user:
                user = staff.user
                
                # 1. Bypass signals completely using .update() for the permission flags
                User.objects.filter(id=user.id).update(is_staff=True, is_superuser=False)
                
                # 2. Force the join-table clear and add (bypasses .set() quirks)
                user.groups.clear()
                user.groups.add(teacher_group)

                # 3. THE FIX: Hunt down the custom dropdown field and force it
                if hasattr(user, 'role'):
                    user.role = 'Teacher'
                    user.save(update_fields=['role'])
                elif hasattr(user, 'user_type'):
                    user.user_type = 'Teacher'
                    user.save(update_fields=['user_type'])
                elif hasattr(user, 'profile') and hasattr(user.profile, 'role'):
                    user.profile.role = 'Teacher'
                    user.profile.save(update_fields=['role'])
                
                updated_count += 1
    
    modeladmin.message_user(request, f"Absolute override successful: {updated_count} staff locked to Teacher (Groups & Profile Dropdown updated).", messages.SUCCESS)

# --- ADMIN CONFIGURATIONS ---

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head_of_department')

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    # 'get_role' will now show the fresh, non-cached data
    list_display = ('staff_id', 'get_username', 'get_name', 'get_role', 'department', 'designation', 'status')
    list_filter = ('department', 'status', 'is_teaching_staff')
    search_fields = ('user__username', 'user__first_name', 'staff_id')
    
    # Updated Action Menu
    actions = [reset_password_to_default, move_to_teacher_role]

    def get_role(self, obj):
        if obj.user:
            # Re-query groups to bypass the Admin's internal cache
            groups = obj.user.groups.all().values_list('name', flat=True)
            return ", ".join(groups) if groups else "No Role Assigned"
        return "No User"
    get_role.short_description = 'Current Role'

    def save_related(self, request, form, formsets, change):
        """
        Forces the absolute role sync AFTER the admin has finished 
        saving Many-to-Many relationships. Bypasses the user.save() entirely.
        """
        super().save_related(request, form, formsets, change)
        
        staff = form.instance
        if staff.user:
            teacher_group, _ = Group.objects.get_or_create(name='Teacher')
            
            # 1. Update permissions directly in the DB (ignores rogue signals)
            User.objects.filter(id=staff.user.id).update(is_staff=True, is_superuser=False)
            
            # 2. Re-fetch to clear and assign groups at the DB level
            user = User.objects.get(pk=staff.user.pk) 
            user.groups.clear()
            user.groups.add(teacher_group)

            # 3. THE FIX: Ensure custom role dropdowns match when saving via form
            if hasattr(user, 'role'):
                user.role = 'Teacher'
                user.save(update_fields=['role'])
            elif hasattr(user, 'user_type'):
                user.user_type = 'Teacher'
                user.save(update_fields=['user_type'])
            elif hasattr(user, 'profile') and hasattr(user.profile, 'role'):
                user.profile.role = 'Teacher'
                user.profile.save(update_fields=['role'])

    def get_name(self, obj):
        return obj.user.get_full_name() if obj.user else "---"
    get_name.short_description = 'Name'

    def get_username(self, obj):
        return obj.user.username if obj.user else "---"
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'

@admin.register(SubjectAllocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ('staff', 'subject', 'classroom')
    list_filter = ('classroom', 'subject')