# mqttclient application command

from django.core.management.base import BaseCommand
from django.conf import settings

from ambulances.management.commands._client import BaseClient

from ambulances.models import Hospital, EquipmentCount, Equipment

# Client
        
class Client(BaseClient):

    # initialization
    def __init__(self,
                 broker,
                 stdout,
                 style,
                 verbosity = 1):

        super().__init__(broker, stdout, style)
        self.verbosity = verbosity
    
    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False
        
        # Subscribing in on_connect() means that if we lose the
        # connection and reconnect then subscriptions will be renewed.
        client.subscribe('#', 2)

        # hospital message handler
        self.client.message_callback_add('hospital/+/#',
                                         self.on_hospital)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("Listening to messages..."))

        return True
        
    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):

        # handle unknown messages
        self.stdout.write(
            self.style.WARNING(
                "*> Unknown message topic {} {}".format(msg.topic,
                                                        msg.payload)))
        
    # Update hospital resources
    def on_hospital(self, client, userdata, msg):

        # parse message
        topic = msg.topic.split('/')
        hospital = topic[1]
        equipment = topic[3]

        if not msg.payload:
            return
        
        quantity = int(msg.payload)

        if self.verbosity > 1:
            self.stdout.write(" > {} {}".format(msg.topic, quantity))

        try:
            
            e = EquipmentCount.objects.get(hospital = hospital,
                                           equipment__name = equipment)

            # update quantity
            if e.quantity != quantity:
                e.quantity = quantity
                e.save()
                if self.verbosity > 0:
                    self.stdout.write(
                        self.style.SUCCESS(">> Hospital '{}' equipment '{}' updated to '{}'".format(e.hospital.name, equipment, quantity)))

        except:

            if self.verbosity > 0:
                self.stdout.write(
                    self.style.ERROR("*> hospital/{}/equipment/{} is not available".format(hospital, equipment)))


class Command(BaseCommand):
    help = 'Connect to the mqtt broker'

    def handle(self, *args, **options):

        broker = {
            'USERNAME': '',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLIENT_ID': 'django',
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)

        verbosity = 1
        if options['verbosity']:
            verbosity = options['verbosity']
        
        client = Client(broker, self.stdout, self.style,
                        verbosity = verbosity)
                
        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
