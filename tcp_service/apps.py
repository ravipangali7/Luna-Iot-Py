from django.apps import AppConfig


class TcpServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tcp_service'
    verbose_name = 'TCP Service (JT808/JT1078)'

    def ready(self):
        pass
