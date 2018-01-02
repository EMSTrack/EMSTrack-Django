import atexit, sys, os

from django.utils.six import BytesIO
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from .management._client import BaseClient
from .models import Ambulance, Equipment, HospitalEquipment, Hospital
from .serializers import AmbulanceSerializer, HospitalSerializer, \
    HospitalEquipmentSerializer


# UpdateClient class

class UpdateClient(BaseClient):

    def publish(self, topic, message, *vargs, **kwargs):
        # increment pubcount then publish
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

@receiver(post_delete, sender=Ambulance)
def mqtt_remove_ambulance(sender, **kwargs):
    obj = kwargs['instance']
    client.remove_topic('ambulance/{}/data'.format(obj.id))


# Hospital signals
    
@receiver(post_save, sender=Hospital)
def mqtt_update_ambulance(sender, **kwargs):
    obj = kwargs['instance']
    client.update_topic('hospital/{}/data'.format(obj.id),
                        HospitalSerializer(obj),
                        qos=2,
                        retain=True)
    
@receiver(post_delete, sender=Hospital)
def mqtt_remove_ambulance(sender, **kwargs):
    obj = kwargs['instance']
    client.remove_topic('hospital/{}/data'.format(obj.id))


# HospitalEquipment signals
    
@receiver(post_save, sender=HospitalEquipment)
def mqtt_update_hospital_equipment(sender, **kwargs):
    obj = kwargs['instance']
    client.update_topic('hospital/{}/equipment/{}'.format(obj.id,
                                                          obj.equipment.name),
                        HospitalEquipmentSerializer(obj),
                        qos=2,
                        retain=True)

@receiver(post_delete, sender=HospitalEquipment)
def mqtt_remove_hospital_equipment(sender, **kwargs):
    obj = kwargs['instance']
    client.remove_topic('hospital/{}/equipment/{}'.format(obj.id,
                                                          obj.equipment.name))
    
