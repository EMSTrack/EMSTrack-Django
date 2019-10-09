import atexit
import logging
import os

from ambulance.serializers import AmbulanceSerializer
from ambulance.serializers import CallSerializer
from equipment.models import Equipment
from equipment.serializers import EquipmentItemSerializer, EquipmentSerializer
from hospital.serializers import HospitalSerializer
from login.serializers import UserProfileSerializer
from login.views import SettingsView
from .client import BaseClient, MQTTException

logger = logging.getLogger(__name__)


# MessagePublishClient class

class MessagePublishClient:

    def publish_message(self, **kwargs):
        pass

    def publish_settings(self, **kwargs):
        pass

    def publish_profile(self, user, **kwargs):
        pass

    def remove_profile(self, user, **kwargs):
        pass

    def publish_ambulance(self, ambulance, **kwargs):
        pass

    def remove_ambulance(self, ambulance, **kwargs):
        pass

    def publish_hospital(self, hospital, **kwargs):
        pass

    def remove_hospital(self, hospital, **kwargs):
        pass

    def publish_equipment_metadata(self, hospital, **kwargs):
        pass

    def publish_equipment_item(self, hospital, **kwargs):
        pass

    def remove_equipment_item(self, hospital, **kwargs):
        pass

    # For calls

    def publish_call(self, call, **kwargs):
        pass

    def remove_call(self, call, **kwargs):
        pass

    def publish_call_status(self, **kwargs):
        pass

    def remove_call_status(self, **kwargs):
        pass


class PublishClient(BaseClient):

    def __init__(self, broker, **kwargs):

        # call super
        super().__init__(broker, **kwargs)

        # set as active
        self.active = True

        # set retry
        self.retry = False

    def on_disconnect(self, client, userdata, rc):
        # Exception is generated only if never connected
        if not self.connected and rc:
            raise MQTTException('Disconnected',
                                rc)
        # call super
        super().on_disconnect(client, userdata, rc)

    def publish_topic(self, topic, payload, qos=0, retain=False):
        if self.active:
            super().publish_topic(topic, payload, qos, retain)

    def remove_topic(self, topic, qos=0):
        if self.active:
            super().remove_topic(topic, qos)

    def publish_message(self, message, qos=2):
        self.publish_topic('message',
                           message,
                           qos=qos,
                           retain=False)

    def publish_settings(self, qos=2, retain=False):
        self.publish_topic('settings',
                           SettingsView.get_settings(),
                           qos=qos,
                           retain=retain)

    def publish_profile(self, user, qos=2, retain=False):
        self.publish_topic('user/{}/profile'.format(user.username),
                           UserProfileSerializer(user),
                           qos=qos,
                           retain=retain)

    def remove_profile(self, user):
        self.remove_topic('user/{}/profile'.format(user.username))

    def publish_ambulance(self, ambulance, qos=2, retain=False):
        self.publish_topic('ambulance/{}/data'.format(ambulance.id),
                           AmbulanceSerializer(ambulance),
                           qos=qos,
                           retain=retain)

    def remove_ambulance(self, ambulance):
        self.remove_topic('ambulance/{}/data'.format(ambulance.id))

    def publish_hospital(self, hospital, qos=2, retain=False):
        self.publish_topic('hospital/{}/data'.format(hospital.id),
                           HospitalSerializer(hospital),
                           qos=qos,
                           retain=retain)

    def remove_hospital(self, hospital):
        self.remove_topic('hospital/{}/data'.format(hospital.id))
        self.remove_topic('equipment/{}/metadata'.format(hospital.equipmentholder.id))

    def publish_equipment_metadata(self, equipmentholder, qos=2, retain=False):
        equipment_items = equipmentholder.equipmentitem_set.values('equipment')
        equipments = Equipment.objects.filter(id__in=equipment_items)
        self.publish_topic('equipment/{}/metadata'.format(equipmentholder.id),
                           EquipmentSerializer(equipments, many=True),
                           qos=qos,
                           retain=retain)

    def publish_equipment_item(self, equipment_item, qos=2, retain=False):
        self.publish_topic('equipment/{}/item/{}/data'.format(equipment_item.equipmentholder.id,
                                                              equipment_item.equipment.id),
                           EquipmentItemSerializer(equipment_item),
                           qos=qos,
                           retain=retain)

    def remove_equipment_item(self, equipment_item):
        self.remove_topic('equipment/{}/item/{}/data'.format(equipment_item.equipmentholder.id,
                                                             equipment_item.equipment.id))

    def publish_call(self, call, qos=2, retain=False):
        # otherwise, publish call data
        self.publish_topic('call/{}/data'.format(call.id),
                           CallSerializer(call),
                           qos=qos,
                           retain=retain)

    def remove_call(self, call):
        # remove ambulancecall status
        for ambulancecall in call.ambulancecall_set.all():
            self.remove_call_status(ambulancecall)

        self.remove_topic('call/{}/data'.format(call.id))

    def publish_call_status(self, ambulancecall, qos=2, retain=False):
        self.publish_topic('ambulance/{}/call/{}/status'.format(ambulancecall.ambulance_id,
                                                                ambulancecall.call_id),
                           ambulancecall.status,
                           qos=qos,
                           retain=retain)

    def remove_call_status(self, ambulancecall):
        self.remove_topic('ambulance/{}/call/{}/status'.format(ambulancecall.ambulance_id,
                                                               ambulancecall.call_id))


# Uses Alex Martelli's Borg for making PublishClient act like a singleton

class SingletonPublishClient(PublishClient):
    _shared_state = {}

    def __init__(self, **kwargs):

        # Makes sure it is a singleton
        self.__dict__ = self._shared_state

        # Do not initialize if already initialized
        if not self.__dict__ == {} and not self.retry:
            # skip initialization
            return

        # initialization
        from django.conf import settings

        broker = {
            'HOST': 'localhost' if not settings.TESTING else settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)

        # override client_id
        broker['CLIENT_ID'] = 'mqtt_publish_' + str(os.getpid())

        try:

            # try to connect
            logger.info('>> Connecting to MQTT brocker...')

            # initialize PublishClient
            super().__init__(broker, **kwargs)

            # wait for connection
            while not self.connected:
                self.loop()

            # start loop
            self.loop_start()

            # register atexit handler to make sure it disconnects at exit
            atexit.register(self.disconnect)

            logger.info(">> Succesfully connected to MQTT brocker '{}'".format(broker))

        except (MQTTException, OSError) as e:

            self.active = False
            self.retry = True

            logger.info(">> Failed to connect to MQTT brocker '{}'. Will retry later...".format(broker))
            logger.info('>> Generated exception: {}'.format(e))

    def disconnect(self):

        # try to connect
        logger.info('<< Disconnecting from MQTT brocker')

        # disconnect
        self.loop_stop()
        super().disconnect()

        # clear dict
        self._shared_state = {}

# mqtt_cache_clear


