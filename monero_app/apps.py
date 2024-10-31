from django.apps import AppConfig

class MoneroAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monero_app'

    def ready(self):
        # Import des signaux pour l'initialiser
        import monero_app.signals
