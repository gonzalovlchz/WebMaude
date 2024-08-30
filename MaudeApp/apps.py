from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.conf import settings

class MaudeappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MaudeApp'

    def ready(self):
        from .models import SiteSetting
        post_migrate.connect(create_default_settings, sender=self)

def create_default_settings(sender, **kwargs):
    from .models import SiteSetting

    # List of default settings to ensure exist in the database
    default_settings = {
        'timeout': settings.DEFAULT_TIMEOUT,  # Example: Default timeout value of 30 seconds
    }

    for key, value in default_settings.items():
        SiteSetting.objects.get_or_create(key=key, defaults={'value': value})

