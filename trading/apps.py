from django.apps import AppConfig


class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading'
    verbose_name = 'مدیریت معاملات'
    
    def ready(self):
        """Import auditlog registration when app is ready."""
        try:
            import trading.auditlog_registration  # noqa
        except ImportError:
            pass

