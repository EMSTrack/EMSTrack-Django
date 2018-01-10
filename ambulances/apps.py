from django.apps import AppConfig

class AmbulancesConfig(AppConfig):
    name = 'ambulances'

    def ready(self):

        # enable django signals
        import ambulances.signals

        # enable mqtt signals
        # if os.environ.get("DJANGO_ENABLE_MQTT_SIGNALS", "True") == "True":

        #     print('importing ambulances.mqtt.publish')
            
        #     import ambulances.mqtt.publish
