import logging
import atexit, sys, os, time

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers

from .client import BaseClient, MQTTException

from ambulance.models import Ambulance
from ambulance.serializers import AmbulanceSerializer

from login.views import SettingsView

from hospital.models import Equipment, HospitalEquipment, Hospital
from hospital.serializers import HospitalSerializer, \
    HospitalEquipmentSerializer, EquipmentSerializer

from login.serializers import ExtendedProfileSerializer

logger = logging.getLogger(__name__)

# MessagePublishClient class

class MessagePublishClient():

    def publish_profile(self, profile, **kwargs):
        pass
        
    def publish_ambulance(self, ambulance, **kwargs):
        pass

    def remove_ambulance(self, ambulance, **kwargs):
        pass
        
    def publish_hospital(self, hospital, **kwargs):
        pass

    def remove_hospital(self, hospital, **kwargs):
        pass
        
    def publish_hospital_metadata(self, hospital, **kwargs):
        pass

    def publish_hospital_equipment(self, hospital, **kwargs):
        pass
        
    def remove_hospital_equipment(self, hospital, **kwargs):
        pass

class PublishClient(BaseClient):

    def __init__(self, broker, **kwargs):

        # call super
        super().__init__(broker, **kwargs)

        # set as active
        self.active = True
    
    def on_disconnect(self, client, userdata, rc):
        # Exception is generated only if never connected
        if not self.connected and rc:
            raise MQTTException('Disconnected',
                                rc)
        # call super
        super().on_disconnect(client, userdata, rc)
    
    def publish_topic(self, topic, payload, qos=0, retain=False):

        if self.active:

            # serializer?
            if isinstance(payload, serializers.BaseSerializer):
                payload = JSONRenderer().render(payload.data)
            else:
                payload = JSONRenderer().render(payload)
                
            # Publish to topic
            self.publish(topic,
                         payload,
                         qos=qos,
                         retain=retain)
        
    def remove_topic(self, topic, qos=0):

        if self.active:
        
            # Publish null to retained topic
            self.publish(topic,
                         None,
                         qos=qos,
                         retain=True)

    def publish_settings(self, qos=2, retain=True):
        self.publish_topic('settings',
                           SettingsView.get_settings(),
                           qos=qos,
                           retain=retain)
        
    def publish_profile(self, profile, qos=2, retain=True):
        self.publish_topic('user/{}/profile'.format(profile.user.username),
                          ExtendedProfileSerializer(profile),
                          qos=qos,
                          retain=retain)
        
    def publish_ambulance(self, ambulance, qos=2, retain=True):
        self.publish_topic('ambulance/{}/data'.format(ambulance.id),
                          AmbulanceSerializer(ambulance),
                          qos=qos,
                          retain=retain)

    def remove_ambulance(self, ambulance):
        self.remove_topic('ambulance/{}/data'.format(ambulance.id))
        
    def publish_hospital(self, hospital, qos=2, retain=True):
        self.publish_topic('hospital/{}/data'.format(hospital.id),
                          HospitalSerializer(hospital),
                          qos=qos,
                          retain=retain)

    def remove_hospital(self, hospital):
        self.remove_topic('hospital/{}/data'.format(hospital.id))
        self.remove_topic('hospital/{}/metadata'.format(hospital.id))
        
    def publish_hospital_metadata(self, hospital, qos=2, retain=True):
        hospital_equipment = hospital.hospitalequipment_set.values('equipment')
        equipment = Equipment.objects.filter(id__in=hospital_equipment)
        self.publish_topic('hospital/{}/metadata'.format(hospital.id),
                          EquipmentSerializer(equipment, many=True),
                          qos=qos,
                          retain=retain)

    def publish_hospital_equipment(self, equipment, qos=2, retain=True):
        self.publish_topic('hospital/{}/equipment/{}/data'.format(equipment.hospital.id,
                                                                 equipment.equipment.name),
                          HospitalEquipmentSerializer(equipment),
                          qos=qos,
                          retain=retain)
        
    def remove_hospital_equipment(self, equipment):
        self.remove_topic('hospital/{}/equipment/{}/data'.format(equipment.hospital.id,
                                                                 equipment.equipment.name))

# Uses Alex Martelli's Borg for making PublishClient act like a singleton

class SingletonPublishClient(PublishClient):

    _shared_state = {}

    def __init__(self, **kwargs):

        # Makes sure it is a singleton
        self.__dict__ = self._shared_state

        # Do not initialize if already initialized
        if not self.__dict__ == {}:
            # skip initialization
            return

        # initialization
        from django.conf import settings
        
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        
        # override client_id
        broker['CLIENT_ID'] = 'mqtt_publish_' + str(os.getpid())
        
        try:

            # try to connect
            logger.info('>> Connecting to MQTT brocker...')
            
            # initialize PublishClient
            super().__init__(broker, **kwargs)

            # wait for connection
            while not self.connected:
                self.loop()

            # start loop
            self.loop_start()

            # register atexit handler to make sure it disconnects at exit
            atexit.register(self.disconnect)

        except MQTTException as e:

            self.active = False
            
            logger.info('>> Failed to connect to MQTT brocker. Will not publish updates to MQTT...')
            logger.info('>> Generated exception: {}'.format(e))
        
