from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from django.conf import settings
from django.utils.functional import wraps

from .models import Status, Ambulances, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, Route, Capability, LocationPoint, User

from .management.mqttupdate import UpdateClient


# Connect to mqtt
def connect_mqtt(model_name, args):

    # Generate (name of) function to call
    func = ("create_" if args['created'] else "edit_") + model_name

    # Instantiate broker
    broker = {
        'USERNAME': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 1883,
        'KEEPALIVE': 60,
        'CLIENT_ID': 'django',
        'CLEAN_SESSION': True
    }

    broker.update(settings.MQTT)

    # Start client
    client = UpdateClient(broker, None, None, func, args['instance'], 0)

    # Loop until client disconnects
    try:
    	client.loop_forever()

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
                pass
        signal_handler(*args, **kwargs)
    return wrapper

@disable_for_loaddata
@receiver(post_delete, sender=Ambulances)
@receiver(post_save, sender=Ambulances)
def ambulance_mqtt_trigger(sender, **kwargs):
    # Connect to mqtt
    connect_mqtt("ambulance", kwargs)

@disable_for_loaddata
@receiver(post_delete, sender=Hospital)
@receiver(post_save, sender=Hospital)
def hospital_mqtt_trigger(sender, **kwargs):
    # Connect to mqtt
    connect_mqtt("hospital", kwargs)

@disable_for_loaddata
@receiver(post_delete, sender=Equipment)
@receiver(post_save, sender=Equipment)
def hospital_equipment_mqtt_trigger(sender, **kwargs):
    connect_mqtt("equipment", kwargs)

@disable_for_loaddata
@receiver(post_delete, sender=EquipmentCount)
@receiver(post_save, sender=EquipmentCount)
def hospital_equipment_count_mqtt_trigger(sender, **kwargs):
    connect_mqtt("equipment_count", kwargs)

@disable_for_loaddata
@receiver(post_save, sender=User)
def user_trigger(sender, **kwargs):
    if kwargs['created']:
        connect_mqtt("user", kwargs)

@disable_for_loaddata
@receiver(m2m_changed, sender=User.ambulances.through)
def user_ambulances_mqtt_trigger(sender, action, instance, **kwargs):
    kwargs['instance'] = instance
    kwargs['created'] = False
    connect_mqtt("user_ambulance_list", kwargs)

@disable_for_loaddata
@receiver(m2m_changed, sender=User.hospitals.through)
def user_hospitals_mqtt_trigger(sender, action, instance, **kwargs):
    kwargs['instance'] = instance
    kwargs['created'] = False
    connect_mqtt("user_hospital_list", kwargs)
