import atexit, sys, os, time

from django.utils.six import BytesIO
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from .mqttclient import BaseClient, MQTTException
from .models import client, Ambulance, Equipment, \
    HospitalEquipment, Hospital
from .serializers import AmbulanceSerializer, HospitalSerializer, \
    HospitalEquipmentSerializer, EquipmentSerializer, \
    ExtendedProfileSerializer

# UpdateClient class

class UpdateClient(BaseClient):

    def on_disconnect(self, client, userdata, rc):
        if rc:
            raise MQTTException('Disconnected',
                                rc)
    
    def publish(self, topic, message, *vargs, **kwargs):
        self.client.publish(topic, message, *vargs, **kwargs)

    def update_topic(self, topic, serializer, qos=0, retain=False):
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

    def update_profile(self, profile, qos=2, retain=True):
        self.update_topic('user/{}/profile'.format(profile.user.username),
                          ExtendedProfileSerializer(profile),
                          qos=qos,
                          retain=retain)
        
    def update_ambulance(self, ambulance, qos=2, retain=True):
        self.update_topic('ambulance/{}/data'.format(ambulance.id),
                          AmbulanceSerializer(ambulance),
                          qos=qos,
                          retain=retain)

    def remove_ambulance(self, ambulance):
        self.remove_topic('ambulance/{}/data'.format(ambulance.id))
        
    def update_hospital(self, hospital, qos=2, retain=True):
        self.update_topic('hospital/{}/data'.format(hospital.id),
                          HospitalSerializer(hospital),
                          qos=qos,
                          retain=retain)

    def remove_hospital(self, hospital):
        self.remove_topic('hospital/{}/data'.format(hospital.id))
        self.remove_topic('hospital/{}/metadata'.format(hospital.id))
        
    def update_hospital_metadata(self, hospital, qos=2, retain=True):
        hospital_equipment = hospital.hospitalequipment_set.values('equipment')
        equipment = Equipment.objects.filter(id__in=hospital_equipment)
        self.update_topic('hospital/{}/metadata'.format(hospital.id),
                          EquipmentSerializer(equipment, many=True),
                          qos=qos,
                          retain=retain)

    def update_hospital_equipment(self, equipment, qos=2, retain=True):
        self.update_topic('hospital/{}/equipment/{}/data'.format(equipment.hospital.id,
                                                                 equipment.equipment.name),
                          HospitalEquipmentSerializer(equipment),
                          qos=qos,
                          retain=retain)
        
    def remove_hospital_equipment(self, equipment):
        self.remove_topic('hospital/{}/equipment/{}/data'.format(equipment.hospital.id,
                                                                 equipment.equipment.name))

# Start client
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
broker['CLIENT_ID'] = 'signals_' + str(os.getpid())

try:

    # try to connect
    print('Connecting to MQTT brocker...')
    local_client = UpdateClient(broker, stdout, style, 0)
    
    # wait for connection
    while not local_client.connected:
        local_client.loop()

    # start loop
    local_client.loop_start()
    
    # register atexit handler to make sure it disconnects at exit
    atexit.register(local_client.disconnect)

    client = local_client
    
except Exception as e:

    print('Could not connect to MQTT brocker. Using dumb client...')

# register signals

# Ambulance signals

# @receiver(post_save, sender=Ambulance)
# def mqtt_update_ambulance(sender, **kwargs):
#     client.client.update_ambulance(kwargs['instance'])

# @receiver(pre_delete, sender=Ambulance)
# def mqtt_remove_ambulance(sender, **kwargs):
#     client.client.remove_ambulance(kwargs['instance'])

# Hospital signals
    
# @receiver(post_save, sender=Hospital)
# def mqtt_update_hospital(sender, **kwargs):
#     client.client.update_hospital(kwargs['instance'])
    
# @receiver(pre_delete, sender=Hospital)
# def mqtt_remove_hospital(sender, **kwargs):
#     client.client.remove_hospital(kwargs['instance'])

# HospitalEquipment signals

# @receiver(post_save, sender=HospitalEquipment)
# def mqtt_update_hospital_equipment(sender, **kwargs):
#     created = kwargs['created']
#     obj = kwargs['instance']
#     client.client.update_hospital_equipment(obj)

#     # update hospital metadata
#     if created:
#         client.client.update_hospital_metadata(Hospital.objects.get(id=obj.hospital.id))

# @receiver(pre_delete, sender=HospitalEquipment)
# def mqtt_remove_hospital_equipment(sender, **kwargs):
#     obj = kwargs['instance']
#     client.client.remove_hospital_equipment(obj)

#     # update hospital metadata
#     client.client.update_hospital_metadata(obj.hospital.id)
