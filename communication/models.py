from django.db import models
from django.contrib.auth.models import User

class BroadcastMessage(models.Model):
    TARGET_CHOICES = [
        ('all_students', 'All Active Students'),
        ('all_parents', 'All Parents'),
        ('all_teachers', 'All Teachers'),
        ('all_staff', 'All Non-Teaching Staff'),
        ('custom', 'Custom Selection'),
    ]

    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_broadcasts')
    message_text = models.TextField()
    target_group = models.CharField(max_length=50, choices=TARGET_CHOICES)
    
    # Statistics
    total_recipients = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Broadcast by {self.sender.username} to {self.target_group} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class CommunicationSettings(models.Model):
    """
    Singleton-like model to store the Third-Party Communication API keys.
    Prevents hardcoding sensitive tokens into the source code.
    """
    PROVIDER_CHOICES = [
        ('none', 'None (Simulation Mode)'),
        ('local', 'Custom Local Node API (Free)'),
        ('ultramsg', 'Ultramsg (Free API)'),
        ('twilio', 'Twilio API'),
        ('meta', 'Meta Cloud API'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='none')
    
    # Common Fields
    api_key = models.CharField(max_length=255, blank=True, null=True, help_text="Twilio Auth Token OR Meta Bearer Token")
    
    # Twilio Specific
    account_sid = models.CharField(max_length=255, blank=True, null=True, help_text="Twilio Account SID (Leave blank if using Meta)")
    
    # Sender Information
    sender_number = models.CharField(max_length=50, blank=True, null=True, help_text="Your Twilio outgoing number (e.g., +123456789) or Meta Phone Number ID")

    class Meta:
        verbose_name = "Communication API Settings"
        verbose_name_plural = "Communication API Settings"

    def __str__(self):
        return f"{self.get_provider_display()} Configuration"

    def save(self, *args, **kwargs):
        # Enforce Singleton Pattern
        if not self.pk and CommunicationSettings.objects.exists():
            # If you try to create a new object but one already exists, 
            # we just override the existing primary key so it updates instead of inserting
            self.pk = CommunicationSettings.objects.first().pk
        super(CommunicationSettings, self).save(*args, **kwargs)
