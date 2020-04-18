from django.apps import AppConfig


class AmbulanceConfig(AppConfig):
    name = 'ambulance'

    def ready(self):

        # enable signals
        from . import signals
