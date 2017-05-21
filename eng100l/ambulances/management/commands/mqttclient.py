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
        self.client.message_callback_add('hospital/+/#',
                                         self.on_hospital)

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

            e = EquipmentCount.objects.get(hospital = hospital,
                                           equipment__name = equipment)

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

    # Update call on database or create new call if doesn't exist
    def on_call(self, client, userdata, msg):
        # parse message
        topic = msg.topic.split('/')
        ambulance_id = topic[1]

        # Parse data into json dict
        stream = BytesIO(msg.payload)
        data = JSONParser().parse(stream)

        if not msg.payload:
            return

        name = data['name']
        residential_unit = data['residential_unit']
        stmain_number = data['stmain_number']
        delegation = data['delegation']        
        zipcode = data['zipcode']
        city = data['city']
        state = data['state']
        location = data['location']
        assignment = data['assignment']
        description = data['description']
        call_time = data['call_time']
        departure_time = data['departure_time']
        transfer_time = data['transfer_time']
        hospital_time = data['hospital_time']
        base_time = data['base_time']


        try:
            call = Call.objects.get(ambulance = ambulance_id)

            # update name
            if(call.name != name):
                call.name = name

            # update residential_unit 
            if(call.residential_unit != residential_unit):
                call.residential_unit = residential_unit

            # update stmain_number
            if(call.stmain_number != stmain_number):
                call.stmain_number = stmain_number

            # update delegation
            if(call.delegation != delegation):
                call.delegation = delegation

            # update zipcode
            if(call.zipcode != zipcode):
                call.zipcode = zipcode

            # update city
            if(call.city != city):
                call.city = city

            # update state
            if(call.state != state):
                call.state = state

            # update location
            if(call.location != location):
                call.location = location

            # update assignment
            if(call.assignment != assignment):
                call.assignment = assignment

            # update description
            if(call.description != description):
                call.description = description

            # update call_time
            if(call.call_time != call_time):
                call.call_time = call_time                 

            # update departure_time
            if(call.departure_time != departure_time):        
                call.departure_time = departure_time

            # update transfer_time
            if(call.transfer_time != transfer_time):        
                call.transfer_time = transfer_time

            # update hospital_time 
            if(call.hospital_time != hospital_time):        
                call.hospital_time = hospital_time

            # update base_time
            if(call.base_time != base_time):        
                call.base_time = base_time
        except Exception:
            self.stdout.write(
                self.style.ERROR(""))
    
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
                lp = serializer.save()

                # Publish ambulance location as soon as user location saved
                self.stdout.write(
                        self.style.SUCCESS(">> LocationPoint for user {} in ambulance {} successfully created.".format(user, ambulance)))
            except Exception:
                self.stdout.write(
                    self.style.ERROR("*> LocationPoint for user {} in ambulance {} failed to create".format(user, ambulance)))

            # Surround with try catch?
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
            status = Status.objects.all().first()
            ambulance.status = status

            # Calculate ambulance orientation?
            ambulance.orientation = 200

            # Save changes made to ambulance
            ambulance.save()

            # Convert obj back to json
            serializer = MQTTAmbulanceLocSerializer(ambulance)
            json = JSONRenderer().render(serializer.data)

            # Publish json - be sure to do this in the seeder
            client.publish('ambulance/{}/location'.format(amb_id), json, qos=2, retain=True)
            client.publish('ambulance/{}/status'.format(amb_id), status.id, qos=2, retain=True)

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
