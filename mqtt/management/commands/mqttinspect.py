import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from mqtt.publish import PublishClient


class Client(PublishClient):

    def __init__(self, broker, **kwargs):

        # retrieve base_topic
        self.base_topic = kwargs.pop('base_topic', '')
        self.timeout = kwargs.pop('timeout', 10)
        self.last_activity = timezone.now()

        # add / if necessary
        if self.base_topic and self.base_topic[-1] != '/':
            self.base_topic += '/'

        # call super
        super().__init__(broker, **kwargs)

    def done(self):
        return (timezone.now() > (self.last_activity +
                                  timedelta(seconds=self.timeout)) and
                super().done())

    def loop(self):

        # start loop
        self.loop_start()

        # are we done yet?
        while not self.done():

            # wait at least until timeout
            remaining = (self.last_activity +
                         timedelta(seconds=self.timeout) -
                         timezone.now())

            # timeout?
            if remaining.total_seconds() > 0:
                if self.verbosity > 0:
                    self.stdout.write(self.style.SUCCESS(">> Waiting for messages. Please be patient."))

                time.sleep(remaining.total_seconds())

        # stop loop
        self.loop_stop()

        if self.verbosity > 0:
            self.stdout.write(
                self.style.SUCCESS("<< End of MQTT topics '{}'.".format(self.base_topic + '#')))

    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        # subscribe to all topics descending from base topic
        self.subscribe(self.base_topic + '#')

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Listening to MQTT topics '{}'...".format(self.base_topic + '#')))

        # last activity
        self.last_activity = timezone.now()

    def on_message(self, client, userdata, msg):

        # retained?
        if msg.retain:

            if self.verbosity > 0:
                self.stdout.write(self.style.SUCCESS(" > {}".format(msg.topic)))
                self.stdout.write("   {}".format(str(msg.payload)))

            # last activity
            self.last_activity = timezone.now()


class Command(BaseCommand):
    help = 'Inspect message on the mqtt broker'

    def add_arguments(self, parser):
        parser.add_argument('--base-topic', nargs='?', default='')
        parser.add_argument('--timeout', nargs='?', type=int, default=10)

    def handle(self, *args, **options):

        import os

        broker = {
            'HOST': settings.MQTT['BROKER_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'mqttinspect_' + str(os.getpid())

        base_topic = options['base_topic']
        timeout = options['timeout']

        client = Client(broker,
                        base_topic=base_topic,
                        timeout=timeout,
                        stdout=self.stdout,
                        style=self.style,
                        verbosity=options['verbosity'])

        try:
            client.loop()

        except KeyboardInterrupt:
            pass

        finally:
            client.wait()
