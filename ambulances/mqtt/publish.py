import atexit, sys, os, time

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from .client import BaseClient, MQTTException

from ..models import client, Ambulance, Equipment, \
    HospitalEquipment, Hospital

from ..serializers import AmbulanceSerializer, HospitalSerializer, \
    HospitalEquipmentSerializer, EquipmentSerializer, \
    ExtendedProfileSerializer

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

class PublishClient(MessagePublishClient, BaseClient):

    def on_disconnect(self, client, userdata, rc):
        # Exception is generated only if never connected
        if not self.connected and rc:
            raise MQTTException('Disconnected',
                                rc)
    
    def publish_topic(self, topic, serializer, qos=0, retain=False):
        # Publish to topic
        self.publish(topic,
                     JSONRenderer().render(serializer.data),
                     qos=qos,
                     retain=retain)
        
    def remove_topic(self, topic, serializer, qos=0):
        # Publish null to retained topic
        self.publish(topic,
                     null,
                     qos=qos,
                     retain=True)

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

# to be used with the lazy constructor
        
def get_client():

    # Start client
    from django.core.management.base import OutputWrapper
    from django.core.management.color import color_style, no_style
    from django.conf import settings

    stdout = OutputWrapper(sys.stdout)
    style = color_style()

    # Instantiate broker
    broker = {
        'HOST': 'localhost',
        'PORT': 1883,
        'KEEPALIVE': 60,
        'CLEAN_SESSION': True
    }

    broker.update(settings.MQTT)
    broker['CLIENT_ID'] = 'mqtt_publish_' + str(os.getpid())

    try:

        # try to connect
        print('Connecting to MQTT brocker...')
        local_client = PublishClient(broker, stdout, style,
                                     verbosity=1, debug=True)

        # wait for connection
        while not local_client.connected:
            local_client.loop()

        # start loop
        local_client.loop_start()

        # register atexit handler to make sure it disconnects at exit
        atexit.register(local_client.disconnect)

    except Exception as e:

        print('Could not connect to MQTT brocker. Using dummy client...')

        local_client = MessagePublishClient()

    return local_client


