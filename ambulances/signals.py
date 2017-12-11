import inspect
import os
import sys
import atexit

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style

from django.conf import settings
from django.utils.functional import wraps

from .models import AmbulanceStatus, Ambulance, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, User

from .management.mqttupdate import UpdateClient

# Are we in loaddata or flush?
enable_signals = os.environ.get("DJANGO_ENABLE_SIGNALS", "True") == "True"

if enable_signals:

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
    def ambulance_mqtt_trigger(sender, **kwargs):
        created = kwargs['created']
        instance = kwargs['instance']

        if(created):
            client.create_ambulance(instance)
        else:
            client.edit_ambulance(instance)

    @receiver(post_delete, sender=Hospital)
    @receiver(post_save, sender=Hospital)
    def hospital_mqtt_trigger(sender, **kwargs):
        created = kwargs['created']
        instance = kwargs['instance']

        if(created):
            client.create_hospital(instance)
        else:
            client.edit_hospital(instance)

    @receiver(post_delete, sender=Equipment)
    @receiver(post_save, sender=Equipment)
    def hospital_equipment_mqtt_trigger(sender, **kwargs):
        created = kwargs['created']
        instance = kwargs['instance']

        if(created):
            client.create_equipment(instance)
        else:
            client.edit_equipment(instance)

    @receiver(post_delete, sender=EquipmentCount)
    @receiver(post_save, sender=EquipmentCount)
    def hospital_equipment_count_mqtt_trigger(sender, **kwargs):

        instance = kwargs['instance']

        if kwargs['created']:
            client.create_equipment_count(instance)
        else:
            client.edit_equipment_count(instance)

    # needs validation
    @receiver(post_save, sender=Call)
    def call_mqtt_trigger(sender, **kwargs):

        instance = kwargs['instance']

        print(instance.active)

        if kwargs['created']:
            client.create_call(instance)  
        else:
            client.edit_call(instance)

    @receiver(post_save, sender=User)
    def user_trigger(sender, **kwargs):

        instance = kwargs['instance']

        if kwargs['created']:
            client.create_user(instance)

#    @receiver(m2m_changed, sender=User.ambulances.through)
#    def user_ambulances_mqtt_trigger(sender, action, instance, **kwargs):
#        client.edit_user_ambulance_list(instance)

#    @receiver(m2m_changed, sender=User.hospitals.through)
#    def user_hospitals_mqtt_trigger(sender, action, instance, **kwargs):
#        client.edit_user_hospital_list(instance)
