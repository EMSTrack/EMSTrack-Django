from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from django.conf import settings

from .models import Status, Ambulances, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, Route, Capability, LocationPoint, User

from .management.commands.mqttupdate import UpdateClient


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


@receiver(post_delete, sender=Ambulances)
@receiver(post_save, sender=Ambulances)
def ambulance_mqtt_trigger(sender, **kwargs):
    # Connect to mqtt
    connect_mqtt("ambulance", kwargs)

@receiver(post_delete, sender=Hospital)
@receiver(post_save, sender=Hospital)
def hospital_mqtt_trigger(sender, **kwargs):
    # Connect to mqtt
    connect_mqtt("hospital", kwargs)

@receiver(post_delete, sender=Equipment)
@receiver(post_save, sender=Equipment)
def hospital_equipment_mqtt_trigger(sender, **kwargs):
    connect_mqtt("equipment", kwargs)

@receiver(post_delete, sender=EquipmentCount)
@receiver(post_save, sender=EquipmentCount)
def hospital_equipment_count_mqtt_trigger(sender, **kwargs):
    connect_mqtt("equipment_count", kwargs)

@receiver(m2m_changed, sender=User.ambulances.through)
@receiver(m2m_changed, sender=User.hospitals.through)
def user_mqtt_trigger(sender, action, instance, **kwargs):
    kwargs['instance'] = instance
    kwargs['created'] = False
    connect_mqtt("user", kwargs)
