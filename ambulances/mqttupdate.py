import atexit, sys, os

from django.utils.six import BytesIO
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from .mqttclient import BaseClient
from .models import Ambulance, Equipment, HospitalEquipment, Hospital
from .serializers import AmbulanceSerializer, HospitalSerializer, \
    HospitalEquipmentSerializer, EquipmentSerializer


# UpdateClient class

class UpdateClient(BaseClient):

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

    def update_hospital_metadata(self, hospital, qos=2, retain=True):
        hospital_equipment = hospital.hospitalequipment_set.values('equipment')
        equipment = Equipment.objects.filter(id__in=hospital_equipment)
        client.update_topic('hospital/{}/metadata'.format(hospital.id),
                            EquipmentSerializer(equipment, many=True),
                            qos=qos,
                            retain=retain)
        
# Loop until client disconnects

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
    
client = UpdateClient(broker, stdout, style, 0)

# register atexit handler to make sure it disconnects at exit
atexit.register(client.disconnect)

# start client on its own thread
client.loop_start()

# register signals

# Ambulance signals

@receiver(post_save, sender=Ambulance)
def mqtt_update_ambulance(sender, **kwargs):
    obj = kwargs['instance']
    client.update_topic('ambulance/{}/data'.format(obj.id),
                        AmbulanceSerializer(obj),
                        qos=2,
                        retain=True)

@receiver(pre_delete, sender=Ambulance)
def mqtt_remove_ambulance(sender, **kwargs):
    obj = kwargs['instance']
    client.remove_topic('ambulance/{}/data'.format(obj.id))


# Hospital signals
    
@receiver(post_save, sender=Hospital)
def mqtt_update_hospital(sender, **kwargs):
    obj = kwargs['instance']
    client.update_topic('hospital/{}/data'.format(obj.id),
                        HospitalSerializer(obj),
                        qos=2,
                        retain=True)
    
@receiver(pre_delete, sender=Hospital)
def mqtt_remove_hospital(sender, **kwargs):
    obj = kwargs['instance']
    client.remove_topic('hospital/{}/data'.format(obj.id))
    client.remove_topic('hospital/{}/metadata'.format(obj.id))


# HospitalEquipment signals

def mqtt_update_hospital_metadata(hospital_id, qos=2, retain=True):
    hospital = Hospital.objects.get(id=hospital_id)
    hospital_equipment = hospital.hospitalequipment_set.values('equipment')
    equipment = Equipment.objects.filter(id__in=hospital_equipment)
    client.update_topic('hospital/{}/metadata'.format(hospital_id),
                        EquipmentSerializer(equipment, many=True),
                        qos=qos,
                        retain=retain)

@receiver(post_save, sender=HospitalEquipment)
def mqtt_update_hospital_equipment(sender, **kwargs):
    created = kwargs['created']
    obj = kwargs['instance']
    client.update_topic('hospital/{}/equipment/{}/data'.format(obj.hospital.id,
                                                               obj.equipment.name),
                        HospitalEquipmentSerializer(obj),
                        qos=2,
                        retain=True)

    # update hospital metadata
    if created:
        hospital = Hospital.objects.get(id=obj.hospital.id)
        client.update_hospital_metadata(hospital,
                                        qos=2,
                                        retain=True)

@receiver(pre_delete, sender=HospitalEquipment)
def mqtt_remove_hospital_equipment(sender, **kwargs):
    obj = kwargs['instance']
    client.remove_topic('hospital/{}/equipment/{}/data'.format(obj.hospital.id,
                                                               obj.equipment.name))

    # update hospital metadata
    mqtt_update_hospital_metadata(obj.hospital.id)
