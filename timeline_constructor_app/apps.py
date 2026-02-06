from django.apps import AppConfig


class TimelineConstructorAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timeline_constructor_app'
    verbose_name = 'Конструктор таймлайнов'

    def ready(self):
        pass
