import atexit
import sys

from .management._client import BaseClient

from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style

from .models import Ambulance, Equipment, HospitalEquipment, Hospital
from .serializers import AmbulanceSerializer, HospitalSerializer, \
    HospitalEquipmentSerializer

from django.conf import settings


# UpdateClient class

class UpdateClient(BaseClient):

    def publish(self, topic, message, *vargs, **kwargs):
        # increment pubcount then publish
        self.client.publish(topic, message, *vargs, **kwargs)

    def update_ambulance(self, obj):
        
        # Publish to ambulance topic
        serializer = AmbulanceSerializer(obj)
        json = JSONRenderer().render(serializer.data)
        self.publish('ambulance/{}/data'.format(obj.id),
                     json,
                     qos=2,
                     retain=True)

    def update_hospital(self, obj):
        
        # Publish to hospital topic
        serializer = HospitalSerializer(obj)
        json = JSONRenderer().render(serializer.data)
        self.publish('hospital/{}/data'.format(obj.id),
                     json,
                     qos=2,
                     retain=True)
        
    def update_hospital_equipment(self, obj):

        # Publish to hospital equipment topic
        serializer = HospitalEquipmentSerializer(obj)
        json = JSONRenderer().render(serializer.data)
        self.publish('hospital/{}/equipment/{}'.format(obj.id,
                                                       obj.equipment.name),
                     json,
                     qos=2,
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

@receiver(post_delete, sender=Ambulance)
@receiver(post_save, sender=Ambulance)
def mqtt_update_ambulance(sender, **kwargs):
    client.update_ambulance(kwargs['instance'])

@receiver(post_delete, sender=HospitalEquipment)
@receiver(post_save, sender=HospitalEquipment)
def mqtt_update_hospital_equipment(sender, **kwargs):
    client.update_hospital_equipment(kwargs['instance'])
