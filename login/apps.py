from django.apps import AppConfig

class LoginConfig(AppConfig):
    name = 'login'

    def ready(self):

        # enable signals
        from . import signals
