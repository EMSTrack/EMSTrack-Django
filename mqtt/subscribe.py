import logging
from io import BytesIO

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from ambulance.models import Ambulance, CallStatus, AmbulanceCallStatus, AmbulanceCall, Waypoint
from ambulance.models import Call
from ambulance.serializers import AmbulanceSerializer, AmbulanceUpdateSerializer, WaypointSerializer
from equipment.models import EquipmentItem
from equipment.serializers import EquipmentItemSerializer
from hospital.models import Hospital
from hospital.serializers import HospitalSerializer
from login.models import Client, ClientLog, ClientStatus, ClientActivity
from login.permissions import cache_clear
from .client import BaseClient

logger = logging.getLogger(__name__)


# Parse exception

class ParseException(Exception):
    pass


# Client exception

class ClientException(Exception):
    pass


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

        # message handler
        self.client.message_callback_add('message',
                                         self.on_message)

        # ambulance handler
        self.client.message_callback_add('user/+/client/+/ambulance/+/data',
                                         self.on_ambulance)

        # # client ambulance status handler
        # self.client.message_callback_add('user/+/client/+/ambulance/+/status',
        #                                  self.on_client_ambulance_status)

        # hospital handler
        self.client.message_callback_add('user/+/client/+/hospital/+/data',
                                         self.on_hospital)

        # hospital equipment handler
        self.client.message_callback_add('user/+/client/+/equipment/+/item/+/data',
                                         self.on_equipment_item)

        # client status handler
        self.client.message_callback_add('user/+/client/+/status',
                                         self.on_client_status)

        # ambulance call handler
        self.client.message_callback_add('user/+/client/+/ambulance/+/call/+/status',
                                         self.on_call_ambulance)

        # ambulance call waypoint handler
        self.client.message_callback_add('user/+/client/+/ambulance/+/call/+/waypoint/+/data',
                                         self.on_call_ambulance_waypoint)

        # subscribe
        self.subscribe('message', 2)
        self.subscribe('user/+/client/+/ambulance/+/data', 2)
        # self.subscribe('user/+/client/+/ambulance/+/status', 2)
        self.subscribe('user/+/client/+/hospital/+/data', 2)
        self.subscribe('user/+/client/+/equipment/+/item/+/data', 2)
        self.subscribe('user/+/client/+/status', 2)
        self.subscribe('user/+/client/+/ambulance/+/call/+/status', 2)
        self.subscribe('user/+/client/+/ambulance/+/call/+/waypoint/+/data', 2)

        logger.info(">> Listening to MQTT messages...")

        return True

    def send_error_message(self, username, client, topic, payload, error, qos=2):

        logger.info("> send_error_message: {}, '{}:{}': '{}'".format(username,
                                                                     topic,
                                                                     payload,
                                                                     error))

        try:

            message = JSONRenderer().render({
                'topic': topic,
                'payload': payload,
                'error': str(error)
            })
            self.publish('user/{}/client/{}/error'.format(username, client.client_id), message, qos=qos)

        except Exception as e:

            logger.warning(('mqtt.SubscribeClient: {}, ' +
                            "topic = '{}:{}', " +
                            "error = '{}', " +
                            "exception = {}").format(username,
                                                     topic,
                                                     payload,
                                                     error,
                                                     e))

    def parse_topic(self, msg, expect, json=True, new_client=False):

        # empty payload ?
        if not msg.payload:
            raise ParseException('Empty payload')

        logger.info(" > Parsing message '{}:{}'".format(msg.topic, msg.payload))

        # empty topic?
        if not msg.topic:
            raise ParseException('Empty topic')

        # parse topic
        values = msg.topic.split('/')

        # not enough topics?
        min_size = expect * 2 - 1
        if len(values) < expect * 2 - 1:
            raise ParseException('Topic with less than size {}'.format(min_size))

        username = '__unknown__'
        try:

            # retrieve user
            username = values[1]

            # print(User.objects.all())
            user = User.objects.get(username=values[1])

        except User.DoesNotExist as e:

            # does not know username
            # cannot send error message to user
            logger.warning(('mqtt.SubscribeClient: {}, ' +
                            "topic = '{}:{}', " +
                            "exception = {}").format(username,
                                                     msg.topic,
                                                     msg.payload,
                                                     e))
            raise ParseException('User does not exist')

        try:

            # retrieve client
            client = Client.objects.get(client_id=values[3])

        except Client.DoesNotExist as e:

            if not new_client:

                # does not know client_id
                # cannot send error message to user
                logger.warning(('mqtt.SubscribeClient: {}, ' +
                                "topic = '{}:{}', " +
                                "exception = {}").format(username,
                                                         msg.topic,
                                                         msg.payload,
                                                         e))
                raise ParseException('Client does not exist')

            else:

                # create new client
                client = Client(client_id=values[3], user=user)

        if json:

            # parse data
            try:

                # Parse data into json dict
                data = JSONParser().parse(BytesIO(msg.payload))

            except Exception as e:

                # send error message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "JSON formatted incorrectly")
                raise ParseException('JSON formatted incorrectly: {}'.format(e))

        else:

            data = msg.payload.decode()

        if expect == 3 and len(values) == 5:

            return user, client, data

        elif expect == 4 and len(values) == 7:

            return user, client, data, values[5]

        elif expect == 5 and len(values) == 9:

            return user, client, data, values[5], values[7]

        elif expect == 6 and len(values) == 11:

            return user, client, data, values[5], values[7], values[9]

        else:

            # send error message to user
            # this should never happen because no subscriptions will match
            # topics with different sizes
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Invalid topic")
            raise ParseException('Invalid topic {}'.format(msg.topic))

    # Update ambulance

    def on_ambulance(self, clnt, userdata, msg):

        try:

            logger.debug("on_ambulance: msg = '{}'".format(msg.topic, msg.payload))

            # parse topic
            user, client, data, ambulance_id = self.parse_topic(msg, 4)

        except Exception as e:

            logger.debug("on_ambulance: ParseException '{}'".format(e))
            return

        try:

            # retrieve ambulance
            logger.debug('ambulance_id = {}'.format(ambulance_id))
            ambulance = Ambulance.objects.get(id=ambulance_id)

        except Ambulance.DoesNotExist:

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Vehicle with id '{}' does not exist".format(ambulance_id))
            return

        except Exception as e:

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        try:

            logger.debug("on_ambulance: ambulance = '{}', data = '{}'".format(ambulance, data))

            # updates must match client
            if client.ambulance != ambulance:
                logger.info("client.ambulance != ambulance ('{}')\nclient = '{}'".format(ambulance, client))
                # send error message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Client '{}' is not currently authorized to update vehicle '{}'"
                                        .format(client.client_id, ambulance.identifier))
                return

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
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_ambulance: EXCEPTION')

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception '{}'".format(e))

        logger.debug('on_ambulance: DONE')

    # Update hospital

    def on_hospital(self, clnt, userdata, msg):

        try:

            logger.debug("on_hospital: msg = '{}:{}'".format(msg.topic, msg.payload))

            # parse topic
            user, client, data, hospital_id = self.parse_topic(msg, 4)

        except Exception as e:

            logger.debug("on_hospital: ParseException '{}'".format(e))
            return

        try:

            # retrieve hospital
            hospital = Hospital.objects.get(id=hospital_id)

        except Hospital.DoesNotExist:

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Hospital with id '{}' does not exist".format(hospital_id))
            return

        except Exception as e:

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        try:

            logger.debug('on_hospital: hospital = {}'.format(hospital))

            # updates must match client
            if client.hospital != hospital:
                # send error message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Client '{}' is not currently authorized to update hospital '{}'"
                                        .format(client.client_id, hospital.name))
                return

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
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_hospital: EXCEPTION')

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception '{}'".format(e))

        logger.debug('on_hospital: DONE')

    # Update equipment

    def on_equipment_item(self, clnt, userdata, msg):

        try:

            logger.debug("on_equipment_item: msg = '{}:{}'".format(msg.topic, msg.payload))

            # parse topic
            user, client, data, equipmentholder_id, equipment_id = self.parse_topic(msg, 5)

        except Exception as e:

            logger.debug("on_equipment_item: ParseException '{}'".format(e))
            return

        try:

            # retrieve hospital equipment
            equipment_item = EquipmentItem.objects.get(equipmentholder_id=equipmentholder_id,
                                                       equipment_id=equipment_id)

        except EquipmentItem.DoesNotExist:

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Equipment with equipmentholder id '{}' and equipment id '{}' does not exist".format(
                                        equipmentholder_id, equipment_id))
            return

        except Exception as e:

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        try:

            logger.debug('on_equipment_item: equipment = {}'.format(equipment_item))

            # update hospital equipment
            serializer = EquipmentItemSerializer(equipment_item,
                                                 data=data,
                                                 partial=True)
            if serializer.is_valid():

                logger.debug('on_equipment_item: valid serializer')

                # save to database
                serializer.save(updated_by=user)

            else:

                logger.debug('on_equipment_item: INVALID serializer')

                # send error message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_equipment_item: EXCEPTION')

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception '{}'".format(e))

        logger.debug('on_equipment_item: DONE')

    # update client information

    def on_client_status(self, clnt, userdata, msg):

        try:

            logger.debug("on_client_status: msg = '{}:{}'".format(msg.topic, msg.payload))

            # parse topic
            user, client, data = self.parse_topic(msg, 3, json=False, new_client=True)

        except Exception as e:

            logger.debug("on_client_status: ParseException '{}'".format(e))
            return

        try:

            # is client online?
            if client.status != ClientStatus.O.name:
                # client is not online
                logger.debug('Client "" is not online'.format(client.client_id))

                # send warning message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Warning: client '{}' is not online".format(client.client_id))

            try:

                # handle status
                status = ClientStatus[data]

            except ValueError as e:

                # send error message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "status '{}' is not valid".format(data))
                return

            logger.debug('on_client_status: status = ' + status.name)

            # create or modify client
            client.status = status.name
            client.save()

        except Exception as e:

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception '{}'".format(e))

        # client is not online
        logger.debug('on_client_status: done')

    # handle calls

    def on_call_ambulance(self, clnt, userdata, msg):

        try:

            logger.debug("on_call_ambulance: msg = '{}:{}'".format(msg.topic, msg.payload))

            # parse topic
            user, client, status, ambulance_id, call_id = self.parse_topic(msg, 5, json=False)

        except Exception as e:

            logger.debug("on_call_ambulance: ParseException '{}".format(e))
            return

        try:

            ambulance = Ambulance.objects.get(id=ambulance_id)
            call = Call.objects.get(id=call_id)
            status = AmbulanceCallStatus[status]

        except Ambulance.DoesNotExist:

            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Vehicle with id '{}' does not exist".format(ambulance_id))
            return

        except Call.DoesNotExist:

            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Call with id '{}' does not exist".format(call_id))
            return

        except Exception as e:

            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        try:

            # Is call ended?
            if call.status == CallStatus.E.name:

                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Call with id '{}' already ended".format(call_id))
                return

            try:

                # Is ambulance part of this call?
                ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance.id)

            except AmbulanceCall.DoesNotExist:

                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Vehicle with id '{}' is not part of call '{}'".format(ambulance_id, call_id))
                return

            if status == AmbulanceCallStatus.A:

                # change ambulancecall status to accepted
                ambulancecall.status = AmbulanceCallStatus.A.name

            elif status == AmbulanceCallStatus.D:

                # change ambulancecall status to decline
                ambulancecall.status = AmbulanceCallStatus.D.name

            elif status == AmbulanceCallStatus.S:

                # change ambulancecall status to suspended
                ambulancecall.status = AmbulanceCallStatus.S.name

            elif status == AmbulanceCallStatus.C:

                # change ambulance status to completed
                ambulancecall.status = AmbulanceCallStatus.C.name

            else:

                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Invalid status '{}'".format(status))
                return

            # save changes
            ambulancecall.save()

        except Exception as e:

            logger.debug('on_call_ambulance: ambulance EXCEPTION')

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))

        logger.debug('on_call_ambulance: DONE')

    # handle calls waypoints

    def on_call_ambulance_waypoint(self, clnt, userdata, msg):

        try:

            logger.debug("on_call_ambulance_waypoint: msg = '{}:{}'".format(msg.topic, msg.payload))

            # parse topic
            user, client, data, ambulance_id, call_id, waypoint_id = self.parse_topic(msg, 6)
            waypoint_id = int(waypoint_id)

        except Exception as e:

            logger.debug("on_call_ambulance_waypoint: ParseException '{}".format(e))
            return

        try:

            ambulance_call = AmbulanceCall.objects.get(ambulance__pk=ambulance_id, call__pk=call_id)

        except Ambulance.DoesNotExist:

            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Vehicle with id '{}' does not exist".format(ambulance_id))
            return

        except Call.DoesNotExist:

            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Call with id '{}' does not exist".format(call_id))
            return

        except Exception as e:

            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return

        try:

            try:

                if waypoint_id > 0:

                    # waypoint exists, update
                    logger.debug('will update waypoint')

                    # retrieve serializer
                    waypoint = Waypoint.objects.get(pk=waypoint_id)

                    # update waypoint
                    serializer = WaypointSerializer(waypoint,
                                                    data=data,
                                                    partial=True)

                else:

                    # waypoint does not exist, create
                    logger.debug('will create waypoint')

                    # create waypoint
                    data['ambulance_call_id'] = ambulance_call.id
                    serializer = WaypointSerializer(data=data)

            except Waypoint.DoesNotExist:

                logger.debug('on_call_ambulance_waypoint: INVALID waypoint id')

                # send error message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Waypoint with id '{}' does not exist".format(waypoint_id))
                return

            except Exception as e:

                self.send_error_message(user, client, msg.topic, msg.payload,
                                        "Exception: '{}'".format(e))
                return

            if serializer.is_valid():

                logger.debug('on_call_ambulance_waypoint: valid serializer')

                if waypoint_id > 0:

                    # save to database
                    serializer.save(updated_by=user, publish=True)

                else:

                    # save to database
                    serializer.save(updated_by=user, ambulance_call_id=ambulance_call.id, publish=True)

            else:

                logger.debug('on_call_ambulance_waypoint: INVALID serializer')

                # send error message to user
                self.send_error_message(user, client, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:

            logger.debug('on_call_ambulance_waypoint: EXCEPTION')

            # send error message to user
            self.send_error_message(user, client, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))

        logger.debug('on_call_ambulance_waypoint: DONE')

    # handle message

    def on_message(self, clnt, userdata, msg):

        try:

            logger.info("on_message: msg = '{}'".format(msg.topic, msg.payload))
            logger.info(" > Parsing message '{}:{}'".format(msg.topic, msg.payload))

            # Parse message
            data = msg.payload.decode()

        except Exception as e:

            logger.debug("on_message: ParseException '{}'".format(e))
            return

        try:

            if data == '"cache_clear"':

                logger.info(" > Clearing cache")

                # call cache clear
                cache_clear()

            else:

                logger.debug("on_message: unknown message '{}'".format(data))

        except Exception as e:

            logger.debug('on_message: EXCEPTION: {}'.format(e))
