from django.apps import AppConfig

class SchoolSystemConfig(AppConfig):
    """
    Master Application Registry for Eduplex.
    This class handles the initialization of core academic 
    and identity protocols.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'school_system'
    verbose_name = 'Eduplex Core System'

    def ready(self):
        """
        The System Ignition Protocol:
        Importing 'signals' here connects the Profile creation 
        and Role-to-Group syncing logic to the Django lifecycle.
        """
        # Ensure signals are imported to register @receiver hooks
        import school_system.signals 
        
        # System Keep-Alive: Initialize background pinger for Render
        from school_system.pinger import start_pinger
        start_pinger()