import logging

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from io import BytesIO

from login.models import Client, ClientLog, ClientStatus
from .client import BaseClient, MQTTException

from ambulance.models import Ambulance
from ambulance.models import Call
from ambulance.serializers import AmbulanceSerializer, AmbulanceUpdateSerializer
from ambulance.serializers import CallSerializer

from hospital.models import Hospital, HospitalEquipment
from hospital.serializers import HospitalSerializer, \
    HospitalEquipmentSerializer

logger = logging.getLogger(__name__)


# SubscribeClient

class SubscribeClient(BaseClient):

    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        # Subscribing in on_connect() means that if we lose the
        # connection and reconnect then subscriptions will be renewed.
        # client.subscribe('#', 2)

        # ambulance handler
        self.client.message_callback_add('user/+/ambulance/+/data',
                                         self.on_ambulance)

        # hospital handler
        self.client.message_callback_add('user/+/hospital/+/data',
                                         self.on_hospital)

        # hospital equipment handler
        self.client.message_callback_add('user/+/hospital/+/equipment/+/data',
                                         self.on_hospital_equipment)

        # call handler
        # self.client.message_callback_add('ambulance/+/call',
        #                                 self.on_call)

        # client status handler
        self.client.message_callback_add('user/+/client/+/status',
                                         self.on_client_status)

        # subscribe
        self.subscribe('user/+/ambulance/+/data', 2)
        self.subscribe('user/+/hospital/+/data', 2)
        self.subscribe('user/+/hospital/+/equipment/+/data', 2)
        self.subscribe('user/+/client/+/status', 2)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Listening to MQTT messages..."))

        return True

    def send_error_message(self, username, topic, payload, error):

        logger.debug("send_error_message: {}, '{}:{}': '{}'".format(username,
                                                                    topic,
                                                                    payload,
                                                                    error))

        if self.verbosity > 0:
            self.stdout.write(self.style.ERROR("*> Error {}, '{}:{}': {}".format(username,
                                                                                 topic,
                                                                                 payload,
                                                                                 error)))

        try:

            message = JSONRenderer().render({
                'topic': topic,
                'payload': payload,
                'error': error
            })
            self.publish('user/{}/error'.format(username), message)

        except Exception as e:

            logger.warning(('mqtt.SubscribeClient: {}, ' +
                            "topic = '{}:{}', " +
                            "error = '{}', " +
                            "exception = {}").format(username,
                                                     topic,
                                                     payload,
                                                     error,
                                                     e))

    def parse_topic(self, msg, json=True):

        if not msg.payload:
            # empty payload
            return

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(" > Parsing message '{}:{}'".format(msg.topic,
                                                                                     msg.payload)))

        # parse topic
        values = msg.topic.split('/')

        # print('values = {}'.format(values))

        try:

            # retrieve user
            # print(User.objects.all())
            user = User.objects.get(username=values[1])

        except ObjectDoesNotExist as e:

            # does not know username
            # cannot send error message to user
            logger.warning(('mqtt.SubscribeClient: {}, ' +
                            "topic = '{}:{}', " +
                            "error = '{}', " +
                            "exception = {}").format(username,
                                                     topic,
                                                     payload,
                                                     error,
                                                     e))
            return

        if json:

            # parse data
            try:

                # Parse data into json dict
                data = JSONParser().parse(BytesIO(msg.payload))

            except Exception as e:

                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        "JSON formatted incorrectly")
                return
        else:

            data = msg.payload.decode()

        if len(values) == 5:

            return user, data, values[3]

        elif len(values) == 7:

            return user, data, values[3], values[5]

        else:

            # send error message to user
            # this should never happen because no subscriptions will match
            # topics with different sizes
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Invalid topic")
            return

    # Update ambulance

    def on_ambulance(self, client, userdata, msg):

        logger.debug("on_ambulance: msg = '{}:{}'".format(msg.topic, msg.payload))

        # parse topic
        values = self.parse_topic(msg)
        if not values:
            return

        logger.debug("on_ambulance: values = '{}'".format(values))

        # retrieve parsed values
        user, data, ambulance_id = values

        try:

            logger.debug('ambulance_id = {}'.format(ambulance_id))

            # retrieve ambulance
            ambulance = Ambulance.objects.get(id=ambulance_id)

        except ObjectDoesNotExist:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Ambulance with id '{}' does not exist".format(ambulance_id))
            return

        except Exception as e:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        logger.debug('on_ambulance: ambulance = {}'.format(ambulance))

        try:

            is_valid = False
            if isinstance(data, (list, tuple)):

                # update ambulances in bulk
                serializer = AmbulanceUpdateSerializer(data=data,
                                                       many=True,
                                                       partial=True)

                if serializer.is_valid():

                    # save to database
                    serializer.save(ambulance=ambulance, updated_by=user)
                    is_valid = True

            else:

                # update ambulance
                serializer = AmbulanceSerializer(ambulance,
                                                 data=data,
                                                 partial=True)

                if serializer.is_valid():

                    # save to database
                    serializer.save(updated_by=user)
                    is_valid = True

            if not is_valid:

                logger.debug('on_ambulance: INVALID serializer')

                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_ambulance: serializer EXCEPTION')

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload, e)

        logger.debug('on_ambulance: DONE')

    # Update hospital
    def on_hospital(self, client, userdata, msg):

        logger.debug("on_hospital: msg = '{}:{}'".format(msg.topic, msg.payload))

        # parse topic
        values = self.parse_topic(msg)
        if not values:
            return

        logger.debug("on_hospital: values = '{}'".format(values))

        # retrieve parsed values
        user, data, hospital_id = values

        try:

            # retrieve hospital
            hospital = Hospital.objects.get(id=hospital_id)

        except ObjectDoesNotExist:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Hospital with id '{}' does not exist".format(hospital_id))
            return

        except Exception as e:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        logger.debug('on_hospital: hospital = {}'.format(hospital))

        try:

            # update hospital
            serializer = HospitalSerializer(hospital,
                                            data=data,
                                            partial=True)
            if serializer.is_valid():

                logger.debug('on_hospital: valid serializer')

                # save to database
                serializer.save(updated_by=user)

            else:

                logger.debug('on_hospital: INVALID serializer')

                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_hospital: serializer EXCEPTION')

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload, e)

        logger.debug('on_hospital: DONE')

    # Update hospital equipment
    def on_hospital_equipment(self, client, userdata, msg):

        logger.debug("on_hospital_equipment: msg = '{}:{}'".format(msg.topic, msg.payload))

        # parse topic
        values = self.parse_topic(msg)
        if not values:
            return

        logger.debug("on_hospital_equipment: values = '{}'".format(values))

        # retrieve parsed values
        user, data, hospital_id, equipment_name = values

        try:

            # retrieve hospital equipment
            hospital_equipment = HospitalEquipment.objects.get(hospital=hospital_id,
                                                               equipment__name=equipment_name)

        except ObjectDoesNotExist:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Hospital equipment with hospital id '{}' and name '{}' does not exist".format(
                                        hospital_id, equipment_name))
            return

        except Exception as e:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        logger.debug('on_hospital_equipment: equipment = {}'.format(hospital_equipment))

        try:

            # update hospital equipment
            serializer = HospitalEquipmentSerializer(hospital_equipment,
                                                     data=data,
                                                     partial=True)
            if serializer.is_valid():

                logger.debug('on_hospital_equipment: valid serializer')

                # save to database
                serializer.save(updated_by=user)

            else:

                logger.debug('on_hospital_equipment: INVALID serializer')

                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_hospital_equipment: serializer EXCEPTION')

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload, e)

        logger.debug('on_hospital_equipment: DONE')

    # update client information
    def on_client_status(self, clnt, userdata, msg):

        logger.debug("on_client_status: msg = '{}:{}'".format(msg.topic, msg.payload))

        # parse topic
        values = self.parse_topic(msg, json=False)
        if not values:
            return

        logger.debug("on_client_status: values = '{}'".format(values))

        # retrieve parsed values
        user, status, client_id = values

        try:

            # handle status
            status = ClientStatus(status)

        except ValueError:

            # client is not online
            logger.debug('on_client_status: invalid status')

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "status'{}' is not valid".format(status))

            return

        # online
        if status == ClientStatus.O:

            # user just logged in, create record
            client = Client(client_id=client_id, user=user, status=status.name)
            client.save()

            # log operation
            log = ClientLog(client=client, action=status.name)
            log.save()

        # offline or disconnected
        elif status == ClientStatus.D or status == ClientStatus.F:

            # user client offline or disconnected
            try:

                # retrieve client record first
                client = Client.objects.get(client_id=client_id)

                # is online?
                if client.status != ClientStatus.O.name:

                    # client is not online
                    logger.debug('on_client_status: not online')

                    # send error message to user
                    self.send_error_message(user, msg.topic, msg.payload,
                                            "client '{}' is not online".format(client_id))

                    return

                # update status
                client.status = status.name
                client.save()

                # log operation
                log = ClientLog(client=client, action=status.name)
                log.save()

                # clean up mqtt topic
                self.remove_topic('/user/{}/client/{}/status'.format(user.username, client_id))

            except Client.DoesNotExist:

                logger.debug('on_client_status: INVALID client')

                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        "client '{}' is not valid".format(client_id))

    # update calls
    def on_call(self, client, userdata, msg):

        logger.debug("on_call: msg = '{}:{}'".format(msg.topic, msg.payload))

        # parse topic
        values = self.parse_topic(msg)
        if not values:
            return

        logger.debug("on_call: values = '{}'".format(values))

        # retrieve parsed values
        user, data, call_id = values

        try:

            logger.debug('call_id = {}'.format(call_id))

            call = Call.objects.get(id=call_id)

        except ObjectDoesNotExist:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Call with id '{}' does not exist".format(call_id))

            return

        except Exception as e:
            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        logger.debug('on_call: call = {}'.format(call))

        try:

            # update call
            serializer = CallSerializer(call)  # TODO: Find structure

            if serializer.is_valid():
                logger.debug('on_call: vaild serializer')

                # save to database
                serializer.save(updated_by=user)

            else:

                logger.debug('on_call: INVALID serializer')

                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_call: serializer EXCEPTION')

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload, e)

        logger.debug('on_call: DONE')
