from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'مدیریت کاربران'
    
    def ready(self):
        """Import signals and auditlog registration when app is ready."""
        import users.signals  # noqa
        try:
            import users.auditlog_registration  # noqa
        except ImportError:
            pass

