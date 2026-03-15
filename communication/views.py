from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
import threading
import requests
import logging

logger = logging.getLogger(__name__)

# Import the utility and model
from .utils import send_whatsapp_message
from .models import BroadcastMessage, CommunicationSettings

# Import models from other apps to get phone numbers
from student_info.models import Student
from staff.models import Staff, Department
from admission.models import ClassRoom
from .forms import CommunicationSettingsForm

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def bulk_whatsapp_view(request):
    """
    View to render the WhatsApp Broadcast form and handle submissions.
    """
    if request.method == 'POST':
        # Get the targeted groups from checkboxes (e.g. ['students', 'parents'])
        target_groups = request.POST.getlist('target_groups')
        message_text = request.POST.get('message_text')
        
        # In the upgraded version, the frontend sends the EXACT phone numbers
        # the user selected from the datatable review screen
        selected_phones = request.POST.getlist('selected_phones[]')
        
        # Fallback if standard array notation wasn't used
        if not selected_phones:
            selected_phones = request.POST.getlist('selected_phones')
        
        if not target_groups or not message_text:
            messages.error(request, "Please select at least one target and provide a message.")
            return redirect('communication:bulk_whatsapp')
            
        if not selected_phones:
            messages.error(request, "Please select at least one valid recipient from the list.")
            return redirect('communication:bulk_whatsapp')
            
        # 1. Clean Phone Numbers (remove duplicates)
        phone_numbers = set(selected_phones)
        
        # 2. Dispatch the Messages (Synchronously or Asynchronously)
        total_recipients = len(phone_numbers)
        
        if total_recipients == 0:
            messages.warning(request, "No valid phone numbers found for the selected groups.")
            return redirect('communication:bulk_whatsapp')

        # Create record first
        broadcast = BroadcastMessage.objects.create(
            sender=request.user,
            message_text=message_text,
            target_group=", ".join(target_groups),
            total_recipients=total_recipients
        )

        # For production, this should be sent to Celery. 
        # For this prototype, we'll do it synchronously or via a basic thread.
        def dispatch_task(phones, msg, broadcast_id):
            logger.info(f"[DISPATCH THREAD STARTED] Processing {len(phones)} numbers.")
            success_count = 0
            for phone in phones:
                try:
                    logger.info(f"[DISPATCH THREAD] Formatting and sending to raw number: {phone}")
                    if send_whatsapp_message(phone, msg):
                        success_count += 1
                except Exception as e:
                    logger.error(f"[DISPATCH THREAD EXCEPTION] Failed on {phone}: {str(e)}")
            
            # Update Statistics
            try:
                bm = BroadcastMessage.objects.get(id=broadcast_id)
                bm.successful_deliveries = success_count
                bm.failed_deliveries = len(phones) - success_count
                bm.save()
                logger.info(f"[DISPATCH THREAD FINISHED] Saved. Success: {bm.successful_deliveries}, Failed: {bm.failed_deliveries}")
            except BroadcastMessage.DoesNotExist:
                logger.error(f"[DISPATCH THREAD DB ERROR] Broadcast ID {broadcast_id} missing on save.")

        # Starting a background thread so the UI doesn't freeze for 100+ requests
        # In a real deployed environment, use Celery or Redis Queue
        thread = threading.Thread(
            target=dispatch_task, 
            args=(list(phone_numbers), message_text, broadcast.id)
        )
        thread.daemon = True
        thread.start()

        messages.success(request, f"WhatsApp Transmission Started! Dispatching {total_recipients} messages in the background.")
        return redirect('communication:bulk_whatsapp')

    # GET Request: Fetch history for the side panel
    history = BroadcastMessage.objects.all()[:10]
    
    # Fetch filter options
    classrooms = ClassRoom.objects.all()
    departments = Department.objects.all()
    
    context = {
        'history': history,
        'classrooms': classrooms,
        'departments': departments,
        'page_title': 'WhatsApp Communication Hub'
    }
    return render(request, 'communication/bulk_whatsapp.html', context)

@login_required
@user_passes_test(is_admin)
def api_settings_view(request):
    """
    View to configure the Twilio/Meta API keys for the WhatsApp tool.
    """
    settings_obj = CommunicationSettings.objects.first()
    
    if request.method == 'POST':
        form = CommunicationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "API Integration Settings successfully updated!")
            return redirect('communication:api_settings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CommunicationSettingsForm(instance=settings_obj)

    context = {
        'form': form,
        'page_title': 'API Communication Settings'
    }
    return render(request, 'communication/api_settings.html', context)

from django.http import JsonResponse

@login_required
@user_passes_test(is_admin)
def whatsapp_pairing_view(request):
    """
    AJAX view to request a WhatsApp Pairing Code from the local Node server.
    """
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if not phone:
            return JsonResponse({'success': False, 'error': 'Phone number is required'})

        try:
            # Ping the local Node service
            response = requests.post(
                "http://localhost:3000/api/link", 
                json={'phone': phone},
                timeout=20
            )
            data = response.json()
            if response.status_code == 200:
                return JsonResponse({'success': True, 'pairing_code': data.get('pairing_code')})
            else:
                return JsonResponse({'success': False, 'error': data.get('error', 'Failed to generate code')})
        except requests.exceptions.ConnectionError:
            return JsonResponse({'success': False, 'error': 'WhatsApp Node Server is not running on port 3000'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def api_filter_users(request):
    """
    AJAX endpoint to return a list of JSON users matching the selected target groups and filters.
    Expects GET or POST data: target_groups[] (list), classroom_id (string/null), department_id (string/null)
    """
    if request.method == 'POST':
        data = request.POST
    else:
        data = request.GET
        
    target_groups = data.getlist('target_groups[]')
    
    # Check if standard list syntax was used instead of array notation
    if not target_groups:
        target_groups = data.get('target_groups', '')
        # Handle cases where it is sent as a comma separated string instead of multiple keys
        if isinstance(target_groups, str) and target_groups:
            target_groups = target_groups.split(',')
        elif not target_groups:
            target_groups = data.getlist('target_groups')
        
    classroom_id = data.get('classroom_id')
    department_id = data.get('department_id')
    
    recipients = []
    
    if 'students' in target_groups:
        qs = Student.objects.filter(is_active=True, primary_phone__isnull=False).exclude(primary_phone='')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
            
        for student in qs:
            recipients.append({
                'id': f"student_{student.id}",
                'name': student.get_full_name,
                'role': f"Student - {student.classroom.name if student.classroom else 'No Class'}",
                'phone': student.primary_phone,
                'type': 'student'
            })
            
    if 'parents' in target_groups:
        qs = Student.objects.filter(is_active=True, emergency_phone__isnull=False).exclude(emergency_phone='')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
            
        for student in qs:
            recipients.append({
                'id': f"parent_{student.id}",
                'name': f"{student.father_name or student.mother_name or 'Parent'} (of {student.get_full_name})",
                'role': 'Parent / Guardian',
                'phone': student.emergency_phone,
                'type': 'parent'
            })
            
    if 'teachers' in target_groups:
        qs = Staff.objects.filter(role='Teacher', status='Active', phone__isnull=False).exclude(phone='')
        if department_id:
            qs = qs.filter(department_id=department_id)
            
        for staff in qs:
            recipients.append({
                'id': f"staff_{staff.id}",
                'name': staff.user.get_full_name(),
                'role': f"Teacher - {staff.department.name if staff.department else 'General'}",
                'phone': staff.phone,
                'type': 'teacher'
            })
            
    if 'staff' in target_groups:
        qs = Staff.objects.exclude(role='Teacher').filter(status='Active', phone__isnull=False).exclude(phone='')
        if department_id:
            qs = qs.filter(department_id=department_id)
            
        for staff in qs:
            recipients.append({
                'id': f"staff_{staff.id}",
                'name': staff.user.get_full_name(),
                'role': f"{staff.get_role_display()} - {staff.department.name if staff.department else 'General'}",
                'phone': staff.phone,
                'type': 'staff'
            })
            
    # Remove obvious duplicates by phone number while preserving original object details
    # We prefer keeping the first instance found
    seen_phones = set()
    unique_recipients = []
    
    for r in recipients:
        phone = str(r['phone']).strip().replace(' ', '')
        if phone not in seen_phones:
            seen_phones.add(phone)
            unique_recipients.append(r)
            
    return JsonResponse({'recipients': unique_recipients})
