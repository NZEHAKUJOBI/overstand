from django.apps import AppConfig


class MediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "media_app"
    verbose_name = "Media Management"

    def ready(self):
        """Import signals when app is ready"""
        # Import signals here if needed
        pass
