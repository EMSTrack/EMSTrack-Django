from django.apps import AppConfig

class AmbulancesConfig(AppConfig):
    name = 'ambulances'

    def ready(self):
        import ambulances.signals
