import logging
import sys
import threading
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


RETRY_TIMER_SECONDS = 3
RETRY_MAX_ATTEMPTS = 10


class BaseClient:

    # initialize client
    def __init__(self, broker, **kwargs):

        # initialize client
        self.broker = broker
        self.transport = kwargs.pop('transport', 'tcp')
        self.tls_set = kwargs.pop('tls_set', {})
        self.tls_insecure = kwargs.pop('tls_insecure', False)
        self.stdout = kwargs.pop('stdout', OutputWrapper(sys.stdout))
        self.style = kwargs.pop('style', color_style())
        self.verbosity = kwargs.pop('verbosity', 1)
        self.debug = kwargs.pop('debug', False)
        # self.forgive_mid = False

        if self.broker['CLIENT_ID']:
            self.client = mqtt.Client(client_id=self.broker['CLIENT_ID'],
                                      clean_session=self.broker['CLEAN_SESSION'],
                                      transport=self.transport)
        else:
            self.client = mqtt.Client()

        # tls_set?
        if self.tls_set:
            self.client.tls_set(**self.tls_set)

        # tls_insecure?
        if self.tls_insecure:
            self.client.tls_insecure_set(True)

        # handle will message
        if 'WILL' in self.broker:
            will = self.broker['WILL']
            self.client.will_set(will['topic'],
                                 payload=will.get('payload', None),
                                 qos=will.get('qos', 2),
                                 retain=will.get('retain', True))

        self.client.on_connect = self.on_connect

        # self.subscribed = {}
        # self.published = {}

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

        # add buffer
        self.buffer = []
        self.number_of_unsuccessful_attempts = 0
        self.buffer_lock = threading.Lock()
        self.publish_lock = threading.Lock()

    def done(self):
        return True

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

    def add_to_buffer(self, topic, payload=None, qos=0, retain=False):

        # acquire lock
        self.buffer_lock.acquire()

        # add to buffer
        self.buffer.append({'topic': topic, 'payload': payload, 'qos': qos, 'retain': retain})

        # release lock
        self.buffer_lock.release()

    def send_buffer(self):

        # acquire lock
        self.buffer_lock.acquire()

        # are there any messages on the buffer?
        while len(self.buffer) > 0:

            logger.debug('> send_buffer len = {}'.format(len(self.buffer)))

            # attempt to send buffered messages
            message = self.buffer.pop(0)

            try:

                # try to publish
                self._publish(**message)

                # reset counter
                self.number_of_unsuccessful_attempts = 0

            except MQTTException:

                logger.debug('could not send message')

                # put message back
                self.buffer.insert(0, message)

                # increment counter
                self.number_of_unsuccessful_attempts += 1

                # set up timer for retrying
                threading.Timer(RETRY_TIMER_SECONDS, self.send_buffer).start()

                # break from loop
                break

        logger.debug('< send_buffer len = {}'.format(len(self.buffer)))

        # release lock
        self.buffer_lock.release()

        if self.number_of_unsuccessful_attempts > RETRY_MAX_ATTEMPTS:
            raise MQTTException('Could not publish to MQTT broker.' +
                                'Tried {} times before failing'.format(self.number_of_unsuccessful_attempts))

    def publish(self, topic, payload=None, qos=0, retain=False):

        try:

            # try to publish
            self._publish(topic, payload, qos, retain)

        except MQTTException:

            # add to buffer
            self.add_to_buffer(topic, payload, qos, retain)

            # set up timer for retrying
            threading.Timer(RETRY_TIMER_SECONDS, self.send_buffer).start()

    def _publish(self, topic, payload=None, qos=0, retain=False):

        # logger.debug('topic = {}'.format(topic))
        # logger.debug('payload = {}'.format(payload))
        # logger.debug('qos = {}'.format(qos))
        # logger.debug('retain = {}'.format(retain))
        result = self.client.publish(topic, payload, qos, retain)
        if result.rc:
            logger.debug('Could not publish to topic (rc = {})'.format(result.rc))
            raise MQTTException('Could not publish to topic (rc = {})'.format(result.rc), result.rc)

    def on_publish(self, client, userdata, mid):
        pass

    def subscribe(self, topic, qos=0):

        # try to subscribe
        result, mid = self.client.subscribe(topic, qos)
        if result:
            raise MQTTException('Could not subscribe to topic',
                                result)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_disconnect(self, client, userdata, rc):
        # logger.debug('disconnecting reason {}'.format(rc))
        self.connected = False

    # disconnect
    def disconnect(self):
        self.client.disconnect()

    def is_connected(self):
        return self.connected

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
    def wait(self, max_tries=10):
        self.disconnect()
        k = 0
        while self.connected and k < max_tries:
            k += 1
            time.sleep(1)

        if self.connected:
            raise MQTTException('Could not disconnect')

    def publish_topic(self, topic, payload, qos=0, retain=False):

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

        # Publish null to retained topic
        self.publish(topic,
                     None,
                     qos=qos,
                     retain=True)
