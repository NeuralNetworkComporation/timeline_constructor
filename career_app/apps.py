from django.apps import AppConfig


class CareerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'career_app'
    verbose_name = 'Карьерный центр'

    def ready(self):
        import career_app.signals