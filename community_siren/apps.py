from django.apps import AppConfig


class CommunitySirenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'community_siren'
    
    def ready(self):
        """Import signals when app is ready"""
        import community_siren.signals  # noqa