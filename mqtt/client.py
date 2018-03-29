import logging
import sys
import time

import paho.mqtt.client as mqtt

from django.core.management.base import OutputWrapper
from django.core.management.color import color_style

from rest_framework import serializers
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)


class MQTTException(Exception):

    def __init__(self, message, value=None):
        super().__init__(message)
        self.value = value


class BaseClient:

    # initialize client
    def __init__(self, broker, **kwargs):

        # initialize client
        self.broker = broker
        self.stdout = kwargs.pop('stdout', OutputWrapper(sys.stdout))
        self.style = kwargs.pop('style', color_style())
        self.verbosity = kwargs.pop('verbosity', 1)
        self.debug = kwargs.pop('debug', False)
        self.forgive_mid = False

        if self.broker['CLIENT_ID']:
            self.client = mqtt.Client(self.broker['CLIENT_ID'],
                                      self.broker['CLEAN_SESSION'])
        else:
            self.client = mqtt.Client()

        # handle will message
        if 'WILL' in self.broker:
            will = self.broker['WILL']
            self.client.will_set(will['topic'],
                                 payload=will.get('payload', None),
                                 qos=will.get('qos', 2),
                                 retain=will.get('retain', True))

        self.client.on_connect = self.on_connect

        self.subscribed = {}
        self.published = {}

        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect

        # default message handler
        self.client.on_message = self.on_message

        if self.broker['USERNAME'] and self.broker['PASSWORD']:
            self.client.username_pw_set(self.broker['USERNAME'],
                                        self.broker['PASSWORD'])

        self.connected = False

        self.client.connect(self.broker['HOST'],
                            self.broker['PORT'],
                            self.broker['KEEPALIVE'])

    def done(self):
        return len(self.published) == 0 and len(self.subscribed) == 0

    def on_connect(self, client, userdata, flags, rc):

        if rc:
            raise MQTTException('Could not connect to brocker (rc = {})'.format(rc),
                                rc)

        self.connected = True

        # success!
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(
                ">> Connected to the MQTT brocker '{}:{}'".format(self.broker['HOST'], 
                                                                  self.broker['PORT'])))

        return True

    def on_message(self, client, userdata, msg):
        pass

    def publish(self, topic, payload=None, qos=0, retain=False):

        # NOTE: The whole forgive mid thing is necessary because
        # on_publish was getting called before publish ended
        # forgive mid if qos = 0
        if qos == 0:
            self.forgive_mid = True

        # try to publish
        result = self.client.publish(topic, payload, qos, retain)
        if result.rc:
            raise MQTTException('Could not publish to topic (rc = {})'.format(result.rc),
                                result.rc)

        if qos != 0:
            # add to dictionary of published
            self.published[result.mid] = (topic, payload, qos, retain)
        else:

            # reset forgive_mid
            self.forgive_mid = False

            # on_published already called?
            if result.mid in self.published:
                if self.published.pop(result.mid) is not None:
                    raise MQTTException('Cannot make sense of mid', result.mid)
            else:
                # add to dictionary of published
                self.published[result.mid] = (topic, payload, qos, retain)

        # debug? 
        if self.debug:
            logger.debug(("Just published '{}[mid={}]:{}'" +
                          "(qos={},retain={})").format(topic,
                                                       result.mid,
                                                       payload,
                                                       qos,
                                                       retain))

    def on_publish(self, client, userdata, mid):

        # debug? 
        if self.debug:
            logger.debug("Published mid={}".format(mid))

        if mid in self.published:
            # remove from list of subscribed
            del self.published[mid]

        else:
            self.published[mid] = None
            if not self.forgive_mid:
                raise MQTTException('Unknown publish mid', mid)

    def subscribe(self, topic, qos=0):

        # try to subscribe
        result, mid = self.client.subscribe(topic, qos)
        if result:
            raise MQTTException('Could not subscribe to topic',
                                result)

        # debug? 
        if self.debug:
            logger.debug("Just subscribed to '{}'[mid={}][qos={}]".format(topic,
                                                                          mid,
                                                                          qos))

        # otherwise add to dictionary of subscribed
        self.subscribed[mid] = (topic, qos)

        # logger.debug('topic = {}, mid = {}'.format(topic, mid))

    def on_subscribe(self, client, userdata, mid, granted_qos):

        # debug? 
        if self.debug:
            logger.debug("Subscribed mid={}, qos={}".format(mid, granted_qos))

        if mid in self.subscribed:
            # remove from list of subscribed
            del self.subscribed[mid]

        else:
            raise MQTTException('Unknown subscribe mid', mid)

    def on_disconnect(self, client, userdata, rc):
        # logger.debug('disconnecting reason {}'.format(rc))
        self.connected = False

    # disconnect
    def disconnect(self):
        self.client.disconnect()

    # loop
    def loop(self, *args, **kwargs):
        self.client.loop(*args, **kwargs)

    # loop_start
    def loop_start(self):
        self.client.loop_start()

    # loop_stop
    def loop_stop(self, *args, **kwargs):
        self.client.loop_stop(*args, **kwargs)

    # loop forever
    def loop_forever(self):
        self.client.loop_forever()

    # wait for disconnect
    def wait(self, MAX_TRIES=10):
        self.disconnect()
        k = 0
        while self.connected and k < MAX_TRIES:
            k += 1
            time.sleep(1)

        if self.connected:
            raise MQTTException('Could not disconnect')

    def publish_topic(self, topic, payload, qos=0, retain=False):

        if self.active:

            # serializer?
            if isinstance(payload, serializers.BaseSerializer):
                payload = JSONRenderer().render(payload.data)
            else:
                payload = JSONRenderer().render(payload)

            # Publish to topic
            self.publish(topic,
                         payload,
                         qos=qos,
                         retain=retain)

    def remove_topic(self, topic, qos=0):

        if self.active:
            # Publish null to retained topic
            self.publish(topic,
                         None,
                         qos=qos,
                         retain=True)
