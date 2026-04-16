from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.admin.sites import NotRegistered

# --- 1. USER & PROFILE MANAGEMENT ---

class ProfileInline(admin.StackedInline):
    from .models import Profile
    model = Profile
    can_delete = False
    verbose_name_plural = 'Role & Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
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

    @admin.action(description="Trigger Secure Password Reset")
    def trigger_password_reset_bulk(self, request, queryset):
        sent_count = 0
        for user in queryset:
            if user.email:
                form = PasswordResetForm({'email': user.email})
                if form.is_valid():
                    form.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='auth/password_reset_email.html',
                        subject_template_name='auth/password_reset_subject.txt',
                    )
                    sent_count += 1
        self.message_user(request, f"Successfully dispatched emails to {sent_count} users.")

    @admin.action(description="Reset Password to Stud1234")
    def reset_passwords_to_default(self, request, queryset):
        student_queryset = queryset.filter(groups__name='Student')
        count = student_queryset.count()
        for user in student_queryset:
            user.set_password('Stud1234')
            user.save()
        
        ignored_count = queryset.count() - count
        msg = f"Reset {count} students. {ignored_count} others ignored."
        self.message_user(request, msg)

# Safer re-registration
try:
    admin.site.unregister(User)
except NotRegistered:
    pass
admin.site.register(User, UserAdmin)


# --- 2. ACADEMIC STRUCTURE ---
from .models import Stream, Subject

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