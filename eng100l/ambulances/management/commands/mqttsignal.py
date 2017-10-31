
from ambulances.management.commands._client import BaseClient

from ambulances.models import Ambulances
from ambulances.serializers import MQTTAmbulanceLocSerializer

from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

class SignalClient(BaseClient):

    def __init__(self,
                 broker,
                 stdout,
                 style,
                 signal_func,
                 id,
                 verbosity = 1):
        super().__init__(broker, stdout, style, verbosity)

        self.signal_func = getattr(self, signal_func)
        self.id = id

    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        self.signal_func(self.id)

        return True


    def create_ambulance(self, id):
        amb = Ambulances.objects.filter(id=id).first()
        print(amb.)

        # Publish location
        serializer = MQTTAmbulanceLocSerializer(amb)
        json = JSONRenderer().render(serializer.data)
        result = self.client.publish('ambulance/{}/location'.format(id), json, qos=2, retain=True)
        print('ambulance/{}/location'.format(id))
        print(result[0])

        # Publish status
        self.client.publish('ambulance/{}/status'.format(id), amb.status.name, qos=2, retain=True)

    def edit_ambulance(self, id):
        amb = Ambulances.objects.filter(id=id).first()
        # TODO
        print("editing")
        self.disconnect()

    # Message publish callback
    def on_publish(self, client, userdata, mid):
        print("published")
        self.disconnect()