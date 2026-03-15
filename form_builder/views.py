from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import CustomForm, FormField, FormSubmission, LogicRule
from .forms import CreateFormForm, AddFieldForm, AddLogicRuleForm, SubmissionReviewForm
import json
import csv
from django.http import HttpResponse, JsonResponse
from django.db.models import Q

# --- SECURITY HELPERS ---
def is_manager(user):
    """Admins, Dept Heads, and Office Staff can manage forms."""
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Dept_Admin', 'Office_Staff']).exists()

# 1. LIST ALL FORMS (Role-Based Visibility)
@login_required
def form_list(request):
    """
    Productivity Filter: 
    - Staff see all (Drafts/Active).
    - Students only see 'Published' forms.
    """
    if is_manager(request.user):
        forms = CustomForm.objects.filter(is_active=True).order_by('-created_at')
    else:
        forms = CustomForm.objects.filter(is_active=True, status='published').order_by('-created_at')
    
    return render(request, 'form_builder/list.html', {'forms': forms, 'is_manager': is_manager(request.user)})

# 2. CREATE A NEW FORM
@login_required
@user_passes_test(is_manager)
def create_form(request):
    if request.method == 'POST':
        form = CreateFormForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.created_by = request.user
            new_form.save()
            messages.success(request, f"Node created: {new_form.title}")
            return redirect('form_builder:builder', form_id=new_form.id)
    else:
        form = CreateFormForm()
    return render(request, 'form_builder/create.html', {'form': form})

# 3. BUILDER (SMART FIELD & LOGIC DESIGNER)
@login_required
@user_passes_test(is_manager)
def form_builder(request, form_id):
    custom_form = get_object_or_404(CustomForm, id=form_id)
    fields = custom_form.fields.all()
    logic_rules = custom_form.logic_rules.all() # Fetch logic rules
    
    field_form = AddFieldForm()
    # Pass the current form instance to restrict logic dropdowns
    logic_form = AddLogicRuleForm(form_instance=custom_form)
    
    if request.method == 'POST':
        # Handle Field Creation
        if 'add_field' in request.POST:
            field_form = AddFieldForm(request.POST)
            if field_form.is_valid():
                new_field = field_form.save(commit=False)
                new_field.custom_form = custom_form
                new_field.save()
                messages.success(request, "Field Node added.")
                return redirect('form_builder:builder', form_id=form_id)
        
        # Handle Logic Rule Creation
        elif 'add_logic' in request.POST:
            logic_form = AddLogicRuleForm(request.POST, form_instance=custom_form)
            if logic_form.is_valid():
                rule = logic_form.save(commit=False)
                rule.form = custom_form
                rule.save()
                messages.success(request, "Conditional Logic branch established.")
                return redirect('form_builder:builder', form_id=form_id)
        
    return render(request, 'form_builder/builder.html', {
        'custom_form': custom_form, 
        'fields': fields,
        'logic_rules': logic_rules,
        'form': field_form,
        'logic_form': logic_form
    })

# 4. RENDER & SUBMIT FORM (With Logic Data Injection)
@login_required
def render_form(request, form_id):
    custom_form = get_object_or_404(CustomForm, id=form_id)
    
    # Check Response Limits (Productivity Guard)
    if custom_form.limit_responses > 0:
        count = FormSubmission.objects.filter(custom_form=custom_form).count()
        if count >= custom_form.limit_responses:
            return render(request, 'error.html', {'message': "This form has reached its maximum response quota."})

    fields = custom_form.fields.all()
    
    # Pack logic rules into JSON for our JavaScript Frontend Engine
    logic_data = []
    for rule in custom_form.logic_rules.all():
        logic_data.append({
            'target': f"field_wrapper_{rule.target_field.id}",
            'trigger': f"field_{rule.trigger_field.id}",
            'action': rule.action,
            'operator': rule.operator,
            'value': rule.value
        })
    
    if request.method == 'POST':
        submission_data = {}
        for field in fields:
            field_name = f"field_{field.id}"
            # Support for File Uploads in JSON Data
            if field.field_type == 'file' and request.FILES.get(field_name):
                # In a production node, you would save to MEDIA and store URL
                file_obj = request.FILES.get(field_name)
                submission_data[field.label] = f"FILE: {file_obj.name}"
            else:
                submission_data[field.label] = request.POST.get(field_name)
        
        FormSubmission.objects.create(
            custom_form=custom_form,
            submitted_by=request.user,
            data=submission_data
        )
        messages.success(request, "Submission registered successfully!")
        return redirect('form_builder:index')

    return render(request, 'form_builder/render.html', {
        'custom_form': custom_form, 
        'fields': fields,
        'logic_json': json.dumps(logic_data) # Inject logic into template
    })

# 5. DELETE FORM
@login_required
def delete_form(request, form_id):
    custom_form = get_object_or_404(CustomForm, id=form_id)
    
    # Only Admin or Creator can delete
    if custom_form.created_by != request.user and not request.user.is_superuser:
        messages.error(request, "Unauthorized request.")
        return redirect('form_builder:index')

    if request.method == 'POST':
        form_name = custom_form.title
        custom_form.delete()
        messages.success(request, f"Node '{form_name}' deleted.")
    
    return redirect('form_builder:index')

# 6. SUBMISSION ANALYTICS & REVIEW LIST
@login_required
@user_passes_test(is_manager)
def form_analytics(request, form_id):
    custom_form = get_object_or_404(CustomForm, id=form_id)
    submissions = FormSubmission.objects.filter(custom_form=custom_form).order_by('-submitted_at')
    
    # Simple JSON data for Chart.js
    analytics_data = {}
    for sub in submissions:
        for label, value in sub.data.items():
            if value: # Ignore empty answers
                if label not in analytics_data:
                    analytics_data[label] = {}
                analytics_data[label][value] = analytics_data[label].get(value, 0) + 1

    context = {
        'form': custom_form,
        'submissions': submissions,
        'total_submissions': submissions.count(),
        'analytics_json': json.dumps(analytics_data),
    }
    return render(request, 'form_builder/analytics.html', context)

# NEW: TOGGLE REVIEW STATUS (Quick Productivity Fix)
@login_required
@user_passes_test(is_manager)
def toggle_review(request, submission_id):
    submission = get_object_or_404(FormSubmission, id=submission_id)
    submission.is_reviewed = not submission.is_reviewed
    submission.reviewed_by = request.user if submission.is_reviewed else None
    submission.save()
    return redirect('form_builder:analytics', form_id=submission.custom_form.id)

# 7. EXPORT TO CSV
@login_required
@user_passes_test(is_manager)
def export_submissions(request, form_id):
    custom_form = get_object_or_404(CustomForm, id=form_id)
    submissions = FormSubmission.objects.filter(custom_form=custom_form)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{custom_form.title}_export.csv"'

    writer = csv.writer(response)
    fields = custom_form.fields.all()
    
    # Headers
    writer.writerow(['User', 'Timestamp', 'Reviewed'] + [f.label for f in fields])

    for sub in submissions:
        row = [
            sub.submitted_by.username if sub.submitted_by else "Guest",
            sub.submitted_at.strftime('%Y-%m-%d %H:%M'),
            "YES" if sub.is_reviewed else "NO"
        ]
        for f in fields:
            row.append(sub.data.get(f.label, ""))
        writer.writerow(row)

    return response