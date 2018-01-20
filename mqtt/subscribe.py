import logging

from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from io import BytesIO

from .client import BaseClient, MQTTException

from ambulance.models import Ambulance
from ambulance.serializers import AmbulanceSerializer

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
        #self.client.message_callback_add('ambulance/+/call',
        #                                 self.on_call)

        # subscribe
        self.subscribe('user/+/ambulance/+/data', 2)
        self.subscribe('user/+/hospital/+/data', 2)
        self.subscribe('user/+/hospital/+/equipment/+/data', 2)
        
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Listening to MQTT messages..."))

        return True

    def send_error_message(self, username, topic, payload, error):

        logger.debug("send_error_message: {}, '{}:{}': '{}'".format(username,
                                                                    topic,
                                                                    payload,
                                                                    error))
        
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

    def parse_topic(self, msg):

        if not msg.payload:
            # empty payload
            return
        
        # parse topic
        values = msg.topic.split('/')

        #print('values = {}'.format(values))
        
        try:

            # retrieve user
            #print(User.objects.all())
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
            
        # parse data
        try:
            
            # Parse data into json dict
            data = JSONParser().parse(BytesIO(msg.payload))
            
        except Exception as e:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "JSON formatted incorrectly")
            return

        if len(values) == 5:

            return (user, data, values[3])
    
        elif len(values) == 7:
            
            return (user, data, values[3], values[5])

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

        try:

            # retrieve parsed values
            user, data, ambulance_id = values
            
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
        
            # update ambulance
            serializer = AmbulanceSerializer(ambulance,
                                             data=data,
                                             partial=True)
            if serializer.is_valid():
                
                logger.debug('on_ambulance: valid serializer')
                
                # save to database
                serializer.save(updated_by=user)
                
            else:
                
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

        # parse topic
        values = self.parse_topic(msg)
        if not values:
            return 
        
        try:

            # retrieve parsed values
            user, data, hospital_id = values
        
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
        
        try:
        
            # update hospital
            serializer = HospitalSerializer(hospital,
                                            data=data,
                                            partial=True)
            if serializer.is_valid():
            
                # save to database
                serializer.save(updated_by=user)

            else:
            
                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        serializer.errors)
        except Exception as e:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload, e)

    # Update hospital equipment
    def on_hospital_equipment(self, client, userdata, msg):

        # parse topic
        values = self.parse_topic(msg)
        if not values:
            return 

        try:

            # retrieve parsed values
            user, data, hospital_id, equipment_name = values
            
            # retrieve hospital equipment
            hospital_equipment = HospitalEquipment.objects.get(hospital=hospital_id,
                                                               equipment__name=equipment_name)

        except ObjectDoesNotExist:

            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Hospital equipment with hospital id '{}' and name '{}' does not exist".format(hospital_id, equipment_name))
            return

        except Exception as e:
        
            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload,
                                    "Exception: '{}'".format(e))
            return
        
        try:
        
            # update hospital equipment
            serializer = HospitalEquipmentSerializer(hospital_equipment,
                                                     data=data,
                                                     partial=True)
            if serializer.is_valid():
                
                # save to database
                serializer.save(updated_by=user)
                
            else:
                
                # send error message to user
                self.send_error_message(user, msg.topic, msg.payload,
                                        serializer.errors)

        except Exception as e:
                            
            # send error message to user
            self.send_error_message(user, msg.topic, msg.payload, e)
