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
        self.timeout = kwargs.pop('timeout', 60)
        self.last_activity = timezone.now()
        
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
                time.sleep(remaining.total_seconds())

        # stop loop
        self.loop_stop()

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Finished cleaning MQTT topics under '{}'...".format(self.base_topic + '/#')))

        
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        # subscribe to all topics descending from base topic
        self.subscribe(self.base_topic + '/#')

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Listening to MQTT topics under '{}'...".format(self.base_topic + '/#')))

        # last activity
        self.last_activity = timezone.now()
        
    def on_message(self, client, userdata, msg):

        # retained?
        if msg.retain:

            # delete topic
            self.remove_topic(msg.topic)
            
            # last activity
            self.last_activity = timezone.now()
                
            if self.verbosity > 0:
                self.stdout.write(self.style.SUCCESS(" > Removing topic '{}'".format(msg.topic)))
                
            
class Command(BaseCommand):
    help = 'Remove retained topics from the mqtt broker'

    def handle(self, *args, **options):

        import os

        broker = {
            'HOST': '127.0.0.1',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'mqttclean_' + str(os.getpid())

        client = Client(broker,
                        stdout = self.stdout,
                        style = self.style,
                        verbosity = options['verbosity'])

        try:
            client.loop()

        except KeyboardInterrupt:
            pass

        finally:
            client.wait()
