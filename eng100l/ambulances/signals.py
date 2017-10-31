from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from django.conf import settings

from .models import Status, Ambulances, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, Route, Capability, LocationPoint, User

from .management.commands.mqttsignal import SignalClient


def connect_mqtt(func, id):
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

    client = SignalClient(broker, None, None, func, id, 0)

    try:
    	client.loop_forever()

    except KeyboardInterrupt:
        pass

    finally:
        client.disconnect()


@receiver(post_delete, sender=Ambulances)
@receiver(post_save, sender=Ambulances)
def ambulances_mqtt_trigger(sender, **kwargs):
    # do mqtt transactions here
    print('Saved: {}'.format(kwargs['instance'].__dict__))

    id = kwargs['instance'].__dict__['id']

    func_name = "create_ambulance" if kwargs['created'] else "edit_ambulance"

    connect_mqtt(func_name, id)