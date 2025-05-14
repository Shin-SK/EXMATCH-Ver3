# --- core/apps.py ---
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals  # シグナルを読み込む
        import core.signals_message  # noqa