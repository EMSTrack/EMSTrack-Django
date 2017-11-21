import inspect
import os

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from django.conf import settings
from django.utils.functional import wraps

from .models import Status, Ambulances, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, Route, Capability, LocationPoint, User

from .management.mqttupdate import UpdateClient

# Instantiate broker
broker = {
    'USERNAME': '',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': 1883,
    'KEEPALIVE': 60,
    'CLIENT_ID': 'os.getpid()',
    'CLEAN_SESSION': True
}

broker.update(settings.MQTT)

# Start client
client = UpdateClient(broker, None, None, 0)

# Loop until client disconnects
try:
    client.loop()

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
    created = kwargs['created']
    instance = kwargs['instance']

    if(created):
        client.create_equipment_count(instance)
    else:
        client.edit_equipment_count(instance)

@receiver(post_save, sender=User)
@disable_for_loaddata
def user_trigger(sender, **kwargs):

    instance = kwargs['instance']

    if kwargs['created']:
        client.create_user(instance)

@receiver(m2m_changed, sender=User.ambulances.through)
@disable_for_loaddata
def user_ambulances_mqtt_trigger(sender, action, instance, **kwargs):
    kwargs['instance'] = instance
    instance = kwargs['instance']
    client.edit_user_ambulance_list(instance)

@receiver(m2m_changed, sender=User.hospitals.through)
@disable_for_loaddata
def user_hospitals_mqtt_trigger(sender, action, instance, **kwargs):
    kwargs['instance'] = instance
    instance = kwargs['instance']
    client.edit_user_hospital_list(instance)
