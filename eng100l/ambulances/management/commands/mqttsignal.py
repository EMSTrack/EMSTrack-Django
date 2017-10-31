
from ambulances.management.commands._client import BaseClient

from ambulances.models import Ambulances

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
        self.disconnect()

        return True


    def create_ambulance(self, id):
        amb = Ambulances.objects.filter(id=id).first()
        print(amb)