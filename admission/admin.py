from django.contrib import admin, messages
from django.contrib.auth.models import User
from .models import ClassRoom, AdmissionApplication, AdmissionDocument
from student_info.models import Student
from unfold.admin import ModelAdmin
from unfold.decorators import action


# ─────────────────────────────────────────
# Shared enrollment helper
# ─────────────────────────────────────────
def _do_enroll(request, apps_queryset):
    """Core logic: convert a queryset of approved applications into Students."""
    success, errors = 0, 0
    for app in apps_queryset:
        if app.status != 'Approved':
            errors += 1
            continue
        try:
            username = f"STU{app.id:04d}"
            if User.objects.filter(username=username).exists():
                username = f"STU{app.id:04d}_{User.objects.count()}"

            user = User.objects.create_user(
                username=username,
                email=app.email,
                password=username,
                first_name=app.student_name.split()[0],
                last_name=" ".join(app.student_name.split()[1:]) if len(app.student_name.split()) > 1 else ""
            )
            Student.objects.create(
                user=user,
                student_id=username,
                classroom=app.class_applied,
                stream=app.stream_applied,
                first_language=app.first_language,
                second_language=app.second_language,
                optional_subject=app.optional_subject,
                date_of_birth=app.date_of_birth,
                gender=app.gender,
                father_name=app.parent_name,
                primary_phone=app.phone,
                address=app.address,
                photo=app.passport_photo
            )
            app.status = 'Admitted'
            app.save()
            success += 1
        except Exception as e:
            errors += 1
            messages.error(request, f"Error enrolling {app.student_name}: {str(e)}")

    if success:
        messages.success(request, f"✅ Successfully enrolled {success} student(s).")
    if errors:
        messages.warning(request, f"⚠️ Skipped {errors} application(s) — only 'Approved' status can be enrolled.")


# ─────────────────────────────────────────
# 1. ClassRoom Admin
# ─────────────────────────────────────────
@admin.register(ClassRoom)
class ClassRoomAdmin(ModelAdmin):
    list_display = ('name', 'standard', 'division', 'stream', 'occupied_seats', 'total_seats', 'get_available_seats')
    list_filter = ('standard', 'stream')
    search_fields = ('name',)
    readonly_fields = ('occupied_seats',)

    @admin.display(description='Available Seats')
    def get_available_seats(self, obj):
        return obj.total_seats - obj.occupied_seats


# ─────────────────────────────────────────
# 2. Document Inline
# ─────────────────────────────────────────
class DocumentInline(admin.TabularInline):
    model = AdmissionDocument
    extra = 0


# ─────────────────────────────────────────
# 3. Admission Application Admin
# ─────────────────────────────────────────
@admin.register(AdmissionApplication)
class ApplicationAdmin(ModelAdmin):
    list_display = ('student_name', 'class_applied', 'parent_name', 'status', 'applied_date')
    list_filter = ('status', 'class_applied')
    search_fields = ('student_name', 'parent_name', 'phone')
    inlines = [DocumentInline]

    # Standard dropdown actions (for selected rows)
    actions = ['approve_selected', 'reject_selected', 'enroll_selected']

    # ── Unfold dedicated "Run" buttons ──────────────────────────────────
    #   actions_list : appear at the TOP of the list (no selection needed)
    #   actions_row  : appear on EACH ROW
    #   actions_detail: appear when VIEWING a single record
    actions_list   = ["run_enroll_all_approved"]
    actions_row    = ["enroll_single"]
    actions_detail = ["enroll_single", "approve_single"]

    # ── TOP‑LEVEL BUTTON: Enroll All Approved (no selection needed) ─────
    @action(description="🚀 Enroll All Approved Applications", url_path="enroll-all")
    def run_enroll_all_approved(self, request):
        """Runs without requiring record selection. Processes all Approved apps."""
        approved_apps = AdmissionApplication.objects.filter(status='Approved')
        if not approved_apps.exists():
            messages.info(request, "No applications with 'Approved' status found.")
            return
        _do_enroll(request, approved_apps)

    # ── ROW BUTTON: Enroll a single application ─────────────────────────
    @action(description="Enroll Student", url_path="enroll")
    def enroll_single(self, request, object_id):
        """Runs on a single specific application from the row or detail view."""
        try:
            app = AdmissionApplication.objects.get(pk=object_id)
            _do_enroll(request, [app])
        except AdmissionApplication.DoesNotExist:
            messages.error(request, "Application not found.")

    # ── DETAIL BUTTON: Approve from within the form ─────────────────────
    @action(description="✓ Approve Application", url_path="approve")
    def approve_single(self, request, object_id):
        """Quick-approve directly from the change form."""
        AdmissionApplication.objects.filter(pk=object_id).update(status='Approved')
        messages.success(request, "Application marked as Approved.")

    # ── DROPDOWN ACTIONS (for legacy checkboxes) ─────────────────────────
    @admin.action(description="Enroll selected Approved applications as Students")
    def enroll_selected(self, request, queryset):
        _do_enroll(request, queryset)

    @admin.action(description="Mark selected as Approved")
    def approve_selected(self, request, queryset):
        queryset.update(status='Approved')

    @admin.action(description="Mark selected as Rejected")
    def reject_selected(self, request, queryset):
        queryset.update(status='Rejected')


# ─────────────────────────────────────────
# 4. Register Documents
# ─────────────────────────────────────────
admin.site.register(AdmissionDocument)