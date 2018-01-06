import time
import paho.mqtt.client as mqtt

class MQTTException(Exception):
    
    def __init__(self, message, value):
        
        super().__init__(message)
        self.value = value

class BaseClient():
    
    # initialize client
    def __init__(self,
                 broker,
                 stdout,
                 style,
                 verbosity = 1):
        

        # initialize client
        self.stdout = stdout
        self.style = style
        self.broker = broker
        self.verbosity = verbosity

        if self.broker['CLIENT_ID']:
            self.client = mqtt.Client(self.broker['CLIENT_ID'],
                                      self.broker['CLEAN_SESSION'])
        else:
            self.client = mqtt.Client()
        self.client.on_connect = self.on_connect

        self.subscribed = {}
        self.published = set()
        
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe

        # default message handler
        self.client.on_message = self.on_message

        if self.broker['USERNAME'] and self.broker['PASSWORD']:
            self.client.username_pw_set(self.broker['USERNAME'],
                                        self.broker['PASSWORD'])

        self.connected = False
        
        self.client.connect(self.broker['HOST'],
                            self.broker['PORT'],
                            self.broker['KEEPALIVE'])

    def on_connect(self, client, userdata, flags, rc):
        
        if rc:
            raise MQTTException('Could not connect to brocker',
                                rc)
        
        self.connected = True
        
        # success!
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Connected to the MQTT brocker '{}:{}'".format(self.broker['HOST'], self.broker['PORT'])))

        return True

    def on_message(self, client, userdata, msg):
        pass

    def on_publish(self, client, userdata, mid):
        pass

    def subscribe(self, topic, qos = 0):

        # try to subscribe
        result, mid = self.client.subscribe(topic, qos)
        if result:
            raise MQTTExpection('Could not subscribe to topic',
                                result)

        # otherwise add to dictionary of subscribed
        self.subscribed[mid] = (topic, qos)

    def on_subscribe(self, client, userdata, mid, granted_qos):

        if mid in self.subscribed:
            # TODO: check granted_qos?
            # remove from list of subscribed
            del self.subscribed[mid]
        
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

    # loop forever
    def loop(self):
        self.client.loop()

    def loop_start(self):
        self.client.loop_start()
