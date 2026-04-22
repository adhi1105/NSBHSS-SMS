import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(phone_number, message_text):
    """
    Utility function to send a WhatsApp message using a third-party API.
    By default, it uses a generic HTTP POST request that you can adapt 
    for Twilio, Meta Cloud API, etc.
    """
    
    # Basic validation
    if not phone_number or not message_text:
        return False
        
    # Clean phone number (remove spaces, etc. Add country code if necessary)
    # This is a basic example. You may need more robust formatting based on your provider.
    cleaned_phone = str(phone_number).replace(' ', '').replace('-', '')
    
    # Fetch Active Settings
    from .models import CommunicationSettings
    settings_obj = CommunicationSettings.objects.first()
    
    if not settings_obj or settings_obj.provider == 'none':
        # Development mode simulation if API is not configured
        logger.info(f"[SIMULATED WHATSAPP] To: {cleaned_phone} | Message: {message_text}")
        return True 

    if settings_obj.provider == 'local':
        return _send_via_local_api(cleaned_phone, message_text)

    if settings_obj.provider == 'twilio':
        return _send_via_twilio(cleaned_phone, message_text, settings_obj)
        
    if settings_obj.provider == 'meta':
        return _send_via_meta_cloud(cleaned_phone, message_text, settings_obj)
        
    if settings_obj.provider == 'ultramsg':
        return _send_via_ultramsg(cleaned_phone, message_text, settings_obj)
        
    return False



# --- Example Provider Specific Implementations ---

def _send_via_local_api(phone, message):
    api_url = "http://localhost:3000/api/send"
    
    payload = {
        "phone": phone,
        "message": message
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=15)
        if response.status_code == 200:
            return True
            
        logger.error(f"[LOCAL API ERR] {response.status_code} - {response.text}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("[LOCAL API REQ FAILED] Node.js server is not running on port 3000.")
        return False
    except Exception as e:
        logger.error(f"[LOCAL API REQ FAILED] {str(e)}")
        return False

def _send_via_ultramsg(phone, message, settings_obj):
    instance_id = settings_obj.account_sid
    token = settings_obj.api_key
    
    if not instance_id or not token:
        logger.error("Ultramsg Config missing Instance ID or Token from DB.")
        return False
        
    if not phone.startswith('+'):
        phone = f"+{phone}"
        
    api_url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    
    payload = {
        "token": token,
        "to": phone,
        "body": message
    }
    
    try:
        response = requests.post(api_url, data=payload, timeout=10)
        if response.status_code in [200, 201]:
            resp_data = response.json()
            if resp_data.get('sent') == 'true' or resp_data.get('message') == 'ok':
                return True
            else:
                logger.error(f"[ULTRAMSG API ERR] Could not verify sent status: {response.text}")
                return False
        else:
            logger.error(f"[ULTRAMSG API ERR] {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"[ULTRAMSG API REQ FAILED] {str(e)}")
        return False

def _send_via_meta_cloud(phone, message, settings_obj):
    sender_id = settings_obj.sender_number
    token = settings_obj.api_key
    
    if not sender_id or not token:
        logger.error("Meta API Key or Sender ID missing from DB config.")
        return False
        
    api_url = f"https://graph.facebook.com/v19.0/{sender_id}/messages"
    
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json'
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {"preview_url": False, "body": message}
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=5)
        if response.status_code in [200, 201]:
            return True
        else:
            logger.error(f"[META CLOUD API ERR] {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"[META CLOUD API REQ FAILED] {str(e)}")
        return False

def _send_via_twilio(phone, message, settings_obj):
    account_sid = settings_obj.account_sid
    auth_token = settings_obj.api_key
    sender_number = settings_obj.sender_number
    
    if not account_sid or not auth_token or not sender_number:
        logger.error("Twilio Config missing from DB.")
        return False
        
    # Twilio API expects form data, not JSON
    api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    # Format according to Twilio specs: "whatsapp:+1234567"
    if not sender_number.startswith('whatsapp:'):
        sender_number = f"whatsapp:{sender_number}"
        
    if not phone.startswith('whatsapp:'):
        # We ensure it has a plus sign
        phone = phone if phone.startswith('+') else f"+{phone}"
        phone = f"whatsapp:{phone}"
        
    payload = {
        'To': phone,
        'From': sender_number,
        'Body': message
    }
    
    try:
        response = requests.post(
            api_url, 
            data=payload, 
            auth=(account_sid, auth_token),
            timeout=5
        )
        if response.status_code in [200, 201]:
            return True
        else:
            logger.error(f"[TWILIO API ERR] {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"[TWILIO API REQ FAILED] {str(e)}")
        return False
