# mqttclient application command

from django.core.management.base import BaseCommand
from django.conf import settings

from ambulances.management.commands._client import BaseClient

from ambulances.models import EquipmentCount, Ambulances, Status
from ambulances.serializers import MQTTLocationSerializer, MQTTAmbulanceLocSerializer

from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer


# Client
class Client(BaseClient):

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
        self.client.message_callback_add('hospital/+/equipment/#',
                                         self.on_hospital)

        # user location handler
        self.client.message_callback_add('user/+/location', self.on_user_loc)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Listening to messages..."))

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

        try:
            quantity = int(msg.payload)
            if self.verbosity > 1:
                self.stdout.write(" > {} {}".format(msg.topic, quantity))

            e = EquipmentCount.objects.get(hospital=hospital,
                                           equipment__name=equipment)

            # update quantity
            if e.quantity != quantity:
                e.quantity = quantity
                e.save()
                if self.verbosity > 0:
                    self.stdout.write(
                        self.style.SUCCESS(">> Hospital '{}' equipment '{}' updated to '{}'".format(e.hospital.name, equipment, quantity)))

        except Exception:
            self.stdout.write(
                self.style.ERROR("*> hospital/{}/equipment/{} is not available".format(hospital, equipment)))


    # Update user location
    def on_user_loc(self, client, userdata, msg):

        topic = msg.topic.split('/')
        user = topic[1]

        if not msg.payload:
            return

        # Parse data into json dict
        stream = BytesIO(msg.payload)
        data = JSONParser().parse(stream)

        # TODO Find out which ambulance is linked to user
        ambulance = 1
        data['ambulance'] = ambulance

        # Serialize data into object
        serializer = MQTTLocationSerializer(data=data)

        if serializer.is_valid():
            try:
                # MAURICIO: Does that save the location to the database? Are we saving the user location as well?
                lp = serializer.save()

                # Publish ambulance location as soon as user location saved
                self.stdout.write(
                        self.style.SUCCESS(">> LocationPoint for user {} in ambulance {} successfully created.".format(user, ambulance)))
            except Exception as e:
                # MAURICIO: added exception to the message
                self.stdout.write(
                    self.style.ERROR("*> LocationPoint for user {} in ambulance {} failed to create. Exception: {}".format(user, ambulance, e)))

            # Surround with try catch?
            # MAURICIO: YES
            self.pub_ambulance_loc(client, ambulance, lp)

        else:
            self.stdout.write(
                self.style.ERROR("*> Input data for user location invalid"))

    # Publish location for ambulance - after ambulance starts querying location table,
    # take out the dependency on the lp generated
    def pub_ambulance_loc(self, client, amb_id, lp):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Publishing location for ambulance {}".format(amb_id)))

        try:
            ambulance = Ambulances.objects.get(id=amb_id)

            # Set status and grab latest location; status should be calculated
            # rather than what this code is doing
            # status = Status.objects.all().first()
            # ambulance.status = status

            # Calculate ambulance orientation?
            ambulance.orientation = 200

            # Save changes made to ambulance
            ambulance.save()

            # Convert obj back to json
            serializer = MQTTAmbulanceLocSerializer(ambulance)
            json = JSONRenderer().render(serializer.data)

            # Publish json - be sure to do this in the seeder
            client.publish('ambulance/{}/location'.format(amb_id), json, qos=2, retain=True)
            client.publish('ambulance/{}/status'.format(amb_id), ambulance.status.name, qos=2, retain=True)

        except Exception as e:
            print(e)
            self.stdout.write(
                self.style.ERROR("*> Ambulance {} does not exist".format(amb_id)))


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

        client = Client(broker, self.stdout, self.style,
                        verbosity = options['verbosity'])

        self.stdout.write(
            self.style.SUCCESS("""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
* * *                    M Q T T   C L I E N T                    * * *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *"""))
        
        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
