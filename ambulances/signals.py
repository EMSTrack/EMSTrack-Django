import inspect
import os
import sys

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style

from django.conf import settings
from django.utils.functional import wraps

from .models import Status, Ambulances, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, Route, Capability, LocationPoint, User

from .management.mqttupdate import UpdateClient

# Are we in loaddata?
is_loaddata = False
for fr in inspect.stack():
    if inspect.getmodulename(fr[1]) == 'loaddata':
        is_loaddata = True
        return

# Loop until client disconnects

# Start client
stdout = OutputWrapper(sys.stdout)
style = color_style()

# Instantiate broker
broker = {
    'USERNAME': '',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': 1883,
    'KEEPALIVE': 60,
    'CLIENT_ID': str(os.getpid()),
    'CLEAN_SESSION': True
}

client = UpdateClient(broker, stdout, style, 0)
broker.update(settings.MQTT)

try:

    client.loop_start()

except KeyboardInterrupt:
    pass

finally:
    client.disconnect()

# function to disable signals when loading data from fixture (loaddata)
def disable_for_loaddata(signal_handler):
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        for fr in inspect.stack():
            if inspect.getmodulename(fr[1]) == 'loaddata':
                return
        signal_handler(*args, **kwargs)
    return wrapper

@receiver(post_delete, sender=Ambulances)
@receiver(post_save, sender=Ambulances)
@disable_for_loaddata
def ambulance_mqtt_trigger(sender, **kwargs):
    created = kwargs['created']
    instance = kwargs['instance']

    if(created):
        client.create_ambulance(instance)
    else:
        client.edit_ambulance(instance)

@receiver(post_delete, sender=Hospital)
@receiver(post_save, sender=Hospital)
@disable_for_loaddata
def hospital_mqtt_trigger(sender, **kwargs):
    created = kwargs['created']
    instance = kwargs['instance']

    if(created):
        client.create_hospital(instance)
    else:
        client.edit_hospital(instance)

@receiver(post_delete, sender=Equipment)
@receiver(post_save, sender=Equipment)
@disable_for_loaddata
def hospital_equipment_mqtt_trigger(sender, **kwargs):
    created = kwargs['created']
    instance = kwargs['instance']

    if(created):
        client.create_equipment(instance)
    else:
        client.edit_equipment(instance)

@receiver(post_delete, sender=EquipmentCount)
@receiver(post_save, sender=EquipmentCount)
@disable_for_loaddata
def hospital_equipment_count_mqtt_trigger(sender, **kwargs):
    
    instance = kwargs['instance']

    if kwargs['created']:
        client.create_equipment_count(instance)
    else:
        client.edit_equipment_count(instance)

# needs validation
@receiver(post_save, sender=Call)
@disable_for_loaddata
def call_mqtt_trigger(sender, **kwargs):
    
    instance = kwargs['instance']

    print(instance.active)

    if kwargs['created']:
        client.create_call(instance)  
    else:
        client.edit_call(instance)

@receiver(post_save, sender=User)
@disable_for_loaddata
def user_trigger(sender, **kwargs):

    instance = kwargs['instance']

    if kwargs['created']:
        client.create_user(instance)

@receiver(m2m_changed, sender=User.ambulances.through)
@disable_for_loaddata
def user_ambulances_mqtt_trigger(sender, action, instance, **kwargs):
    client.edit_user_ambulance_list(instance)

@receiver(m2m_changed, sender=User.hospitals.through)
@disable_for_loaddata
def user_hospitals_mqtt_trigger(sender, action, instance, **kwargs):
    client.edit_user_hospital_list(instance)
