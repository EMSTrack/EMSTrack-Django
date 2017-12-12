# mqttclient application command

from django.core.management.base import BaseCommand
from django.conf import settings

from ambulances.management._client import BaseClient

from ambulances.models import EquipmentCount, Ambulance, Status, Call, User, Hospital
from ambulances.serializers import MQTTLocationSerializer, MQTTAmbulanceLocSerializer, CallSerializer, MQTTUserLocationSerializer

from django.utils.six import BytesIO
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point
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

        # call handler
        self.client.message_callback_add('ambulance/+/call', self.on_call)

        # user location handler
        self.client.message_callback_add('user/+/location', self.on_user_loc)

        # status handler
        self.client.message_callback_add('user/+/status', self.on_user_status)

        # ambulance linking handler
        self.client.message_callback_add('user/+/ambulance', self.on_amb_sel)

        # ambulance linking handler
        self.client.message_callback_add('user/+/hospital', self.on_hosp_sel)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Listening to messages..."))

        return True

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):

        # handle unknown messages
        self.stdout.write(
            self.style.WARNING(
                "*> Ignoring message topic {} {}".format(msg.topic,
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

    # Update call on database or create new call if doesn't exist
    def on_call(self, client, userdata, msg):
        # parse message
        topic = msg.topic.split('/')
        ambulance_id = topic[1]

        if not msg.payload:
            return

        try:
            # Parse data into json dict
            stream = BytesIO(msg.payload)
            data = JSONParser().parse(stream)
            # data.pop("id", None)
        except Exception:
            self.stdout.write(self.style.ERROR("ERROR PARSING CALL JSON"))

        # Obtain call ID to update/create
        id = data["id"]

        # Obtain ambulance
        try:
            amb = Ambulance.objects.get(id=ambulance_id)
        except ObjectDoesNotExist as e:
            self.stdout.write(self.style.ERROR("Ambulance {} does not exist".format(ambulance_id)))
            return

        # Obtain call object
        call = Call.objects.filter(id=id).first()

        serializer = None
        success_text = ">> Updated call {} in database"
        failure_text = "*> Failed to update call {} in database"

        exists = False

        # Should never run because all calls originate from a POST request to the server (unless this is changed)
        if call is None:
            serializer = CallSerializer(data=data)
            success_text = ">> Created call {} in database"
            failure_text = "*> Failed to create call {} in database"

        # If the call does exist, update it
        else:
            serializer = CallSerializer(data=data)
            exists = True

        try:
            if serializer.is_valid(raise_exception=True):
                try:
                    if exists:
                        latitude = data.pop('latitude')
                        longitude = data.pop('longitude')

                        location = Point(longitude, latitude)
                        data['location'] = location

                        Call.objects.filter(id=id).update(**data)
                        # call = serializer.update(instance=call, validated_data=serializer.validated_data)
                    else:
                        call = serializer.save()

                    self.stdout.write(self.style.SUCCESS(success_text.format(call.id)))
                except Exception as e:
                    print(e)
                    self.stdout.write(self.style.ERROR(failure_text.format(call.id)))
        except Exception as e:
            print(e)
            self.stdout.write(self.style.ERROR("*> Error with data format"))

    # Update user location
    def on_user_loc(self, client, userdata, msg):

        topic = msg.topic.split('/')
        username = topic[1]
        user = User.objects.get(username=username)

        if not msg.payload:
            return

        try:
            # Parse data into json dict
            stream = BytesIO(msg.payload)
            data = JSONParser().parse(stream)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR("*> JSON formatted incorrectly: {}".format(msg.payload)))
            return

        # has ambulance?
        if not user.ambulance:
            self.stdout.write(
                self.style.ERROR("*> User '{}' is not currently assigned to any ambulances.".format(username)))
            return
            
        # TODO Find out which ambulance is linked to user
        ambulance = user.ambulance.id

        try:
            data['user'] = user.id
            data['ambulance'] = ambulance
        except TypeError:
            self.stdout.write(
                self.style.ERROR("*> Failed to assign ambulance to location point. {} is formatted incorrectly.".format(msg.payload)))
            return

        # Serialize data into object
        serializer = MQTTUserLocationSerializer(data=data)

        if serializer.is_valid():
            try:
                # MAURICIO: Does that save the location to the database? Are we saving the user location as well?
                lp = serializer.save()

                # Publish ambulance location as soon as user location saved
                try:
                    self.pub_ambulance_loc(client, ambulance, lp)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR("*> Failed to publish location. Exception: {}".format(e)))

                self.stdout.write(
                        self.style.SUCCESS(">> LocationPoint for user {} in ambulance {} successfully created.".format(username, ambulance)))
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR("*> LocationPoint for user {} in ambulance {} failed to create. Exception: {}".format(username, ambulance, e)))

        else:
            self.stdout.write(
                self.style.ERROR("*> Input data for user location invalid"))

    # Publish location for ambulance - after ambulance starts querying location table,
    # take out the dependency on the lp generated
    def pub_ambulance_loc(self, client, amb_id, lp):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Publishing location for ambulance {}".format(amb_id)))

        try:
            # Set status and grab latest location; status should be calculated
            # rather than what this code is doing
            # status = Status.objects.all().first()
            # ambulance.status = status

            # Calculate ambulance orientation?

            # Save changes made to ambulance
            # Ambulance.objects.filter(id=user.ambulance.id).update(orientation=200)

            # query for the ambulance
            ambulance = Ambulance.objects.get(id=amb_id)

            # Convert obj back to json
            serializer = MQTTAmbulanceLocSerializer(ambulance)
            json = JSONRenderer().render(serializer.data)

            # Publish json - be sure to do this in the seeder
            client.publish('ambulance/{}/location'.format(amb_id), json, qos=2, retain=True)
            # client.publish('ambulance/{}/status'.format(amb_id), ambulance.status.name, qos=2, retain=True)

        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR("*> Ambulance {} does not exist".format(amb_id)))

        except Exception as e:
            print(e)
            self.stdout.write(
                self.style.ERROR("Error parsing data"))

    # Update status from dispatch team
    def on_user_status(self, client, userdata, msg):
        topic = msg.topic.split('/')
        username = topic[1]
        user = User.objects.get(username=username)

        if not msg.payload:
            return

        status_str = msg.payload.decode("utf-8")

        try:
            status = Status.objects.get(name=status_str)
            Ambulance.objects.filter(id=user.ambulance.id).update(status=status)
            self.stdout.write(self.style.SUCCESS(
                ">> Successful status update: {} for ambulance {}").format(status_str, user.ambulance.id))

        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR("*> Status {} does not exist".format(status_str)))
            return

        except Exception as e:
            print(e)
            self.stdout.write(
                self.style.ERROR("*> Error saving status for ambulance {}".format(user.ambulance.id)))

    def on_amb_sel(self, client, userdata, msg):
        topic = msg.topic.split('/')
        username = topic[1]

        if not msg.payload:
            return

        amb_id = int(msg.payload.decode("utf-8"))

        # Obtain user
        user = User.objects.filter(username=username)
        if not user:
            self.stdout.write(
                self.style.ERROR("*> User {} does not exist".format(username)))
            return

        try:
            # If -1 is published to topic, unhook user from any ambulance
            if amb_id < 0:
                user.update(ambulance=None)
            else:
                user.update(ambulance=Ambulance.objects.get(id=amb_id))

            self.stdout.write(self.style.SUCCESS(
                ">> Successfully hooked user {} to ambulance {}").format(username, amb_id))

        except ObjectDoesNotExist:
                self.stdout.write(
                    self.style.ERROR("*> Ambulance {} does not exist".format(amb_id)))

        except Exception as e:
            print(e)
            self.stdout.write(
                self.style.ERROR("*> Error saving ambulance for user {}".format(username)))


    def on_hosp_sel(self, client, userdata, msg):
        topic = msg.topic.split('/')
        username = topic[1]

        if not msg.payload:
            return

        try:
            hosp_id = int(msg.payload.decode("utf-8"))
        except ValueError:
            self.stdout.write(
                self.style.ERROR("*> {} is not an int".format(msg.payload)))
            return

        # Obtain user
        user = User.objects.filter(username=username)
        if not user:
            self.stdout.write(
                self.style.ERROR("*> User {} does not exist".format(username)))
            return

        try:
            if hosp_id < 0:
                user.update(hospital=None)
            else:
                user.update(hospital=Hospital.objects.get(id=hosp_id))

            self.stdout.write(self.style.SUCCESS(
                ">> Successfully hooked user {} to hospital {}").format(username, hosp_id))

        except ObjectDoesNotExist:
                self.stdout.write(
                    self.style.ERROR("*> Hospital {} does not exist".format(hosp_id)))

        except Exception as e:
            print(e)
            self.stdout.write(
                self.style.ERROR("*> Error saving hospital for user {}".format(username)))



class Command(BaseCommand):
    help = 'Connect to the mqtt broker'

    def handle(self, *args, **options):

        import os
        
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
        broker['CLIENT_ID'] = broker['CLIENT_ID'] + '_' + str(os.getpid())

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
