from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.admin.sites import NotRegistered
from django.db import transaction
from .models import Profile, Stream, Subject

# Safe import for Unfold Auth Admin
try:
    from unfold.contrib.auth.admin import UserAdmin as UnfoldUserAdmin
    from unfold.decorators import action as unfold_action
    HAS_UNFOLD = True
except ImportError:
    from django.contrib.auth.admin import UserAdmin as UnfoldUserAdmin
    unfold_action = None
    HAS_UNFOLD = False

# --- 1. USER & PROFILE MANAGEMENT ---

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Role & Profile'
    fk_name = 'user'

class MyUserAdmin(UnfoldUserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    actions = ['trigger_password_reset_bulk', 'reset_passwords_to_default']
    
    def get_role(self, instance):
        if hasattr(instance, 'profile'):
            return instance.profile.role
        return '-'
    get_role.short_description = 'Role'

    # Action 1: Bulk Email reset (Secure)
    def trigger_password_reset_bulk(self, request, queryset):
        """Dispatches branded password reset emails to selected users."""
        sent_count = 0
        users_with_email = queryset.exclude(email__isnull=True).exclude(email__exact='')
        
        with transaction.atomic():
            for user in users_with_email:
                form = PasswordResetForm({'email': user.email})
                if form.is_valid():
                    form.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='auth/password_reset_email.html',
                        subject_template_name='auth/password_reset_subject.txt',
                    )
                    sent_count += 1
        
        self.message_user(request, f"🚀 Successfully dispatched secure reset emails to {sent_count} users.")
    trigger_password_reset_bulk.short_description = "Trigger Secure Password Reset"

    # Action 2: Reset to Stud1234 (Mass Default - Optimized)
    def reset_passwords_to_default(self, request, queryset):
        """Forcibly sets password to 'Stud1234' for selected Students only."""
        # FIX: Filter by profile role 'Student' instead of group membership
        student_queryset = queryset.filter(profile__role='Student')
        count = student_queryset.count()
        
        if count == 0:
            self.message_user(request, "⚠️ No users with the Student role were found among your selection.", level='warning')
            return

        with transaction.atomic():
            for user in student_queryset:
                user.set_password('Stud1234')
                user.save()
        
        ignored_count = queryset.count() - count
        msg = f"✅ Successfully reset {count} student(s) to 'Stud1234'."
        if ignored_count > 0:
            msg += f" {ignored_count} non-student users were skipped for security."
            
        self.message_user(request, msg)
    reset_passwords_to_default.short_description = "Reset Password to Stud1234"

    # Apply Unfold decorations if available
    if HAS_UNFOLD and unfold_action:
        trigger_password_reset_bulk = unfold_action(
            description="Trigger Secure Password Reset", 
            icon="mail"
        )(trigger_password_reset_bulk)
        
        reset_passwords_to_default = unfold_action(
            description="Reset Password to Stud1234", 
            icon="lock_reset"
        )(reset_passwords_to_default)

# --- SAFER RE-REGISTRATION ---
try:
    admin.site.unregister(User)
except NotRegistered:
    pass

admin.site.register(User, MyUserAdmin)


# --- 2. ACADEMIC STRUCTURE ---

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject_code', 'subject_type', 'is_practical')
    list_filter = ('subject_type', 'is_practical', 'streams')
    search_fields = ('name', 'subject_code')
    filter_horizontal = ('streams',)