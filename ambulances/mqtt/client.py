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
                 verbosity = 1,
                 **kwargs):
        

        # initialize client
        self.stdout = stdout
        self.style = style
        self.broker = broker
        self.verbosity = verbosity

        self.debug = kwargs.pop('debug', False)
        
        if self.broker['CLIENT_ID']:
            self.client = mqtt.Client(self.broker['CLIENT_ID'],
                                      self.broker['CLEAN_SESSION'])
        else:
            self.client = mqtt.Client()
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

    def on_connect(self, client, userdata, flags, rc):
        
        if rc:
            raise MQTTException('Could not connect to brocker (rc = {})'.format(rc),
                                rc)
        
        self.connected = True
        
        # success!
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Connected to the MQTT brocker '{}:{}'".format(self.broker['HOST'], self.broker['PORT'])))

        return True

    def on_message(self, client, userdata, msg):
        pass

    def publish(self, topic, payload = None, qos = 0, retain = False):
        
        # try to publish
        result = self.client.publish(topic, payload, qos, retain)
        print("> result = {}".format(result))
        
        if result.rc:
            raise MQTTException('Could not publish to topic (rc = {})'.format(result.rc),
                                result.rc)

        # debug? 
        if self.debug:
            print("> Just published '{}[mid={}]:{}'(qos={},retain={})".format(topic,
                                                                          result.mid,
                                                                          payload,
                                                                          qos,
                                                                          retain))
            
        # otherwise add to dictionary of published
        self.published[result.mid] = (topic, payload, qos, retain)

        #print('topic = {}, result = {}'.format(topic, result))

    def on_publish(self, client, userdata, mid):

        # debug? 
        if self.debug:
            print("> Published mid={}".format(mid))
                  
        if mid in self.published:
            # TODO: check granted_qos?
            # remove from list of subscribed
            del self.published[mid]

        else:
            raise MQTTException('Unknown publish mid', mid)

    def subscribe(self, topic, qos = 0):

        # try to subscribe
        result, mid = self.client.subscribe(topic, qos)
        if result:
            raise MQTTException('Could not subscribe to topic',
                                result)

        # debug? 
        if self.debug:
            print("> Just subscribed to '{}'[mid={}][qos={}]".format(topic,
                                                                     mid,
                                                                     qos))
            
            
        # otherwise add to dictionary of subscribed
        self.subscribed[mid] = (topic, qos)

        #print('topic = {}, mid = {}'.format(topic, mid))

    def on_subscribe(self, client, userdata, mid, granted_qos):

        # debug? 
        if self.debug:
            print("> Subscribed mid={}, qos={}".format(mid, granted_qos))
        
        if mid in self.subscribed:
            # TODO: check granted_qos?
            # remove from list of subscribed
            del self.subscribed[mid]

        else:
            raise MQTTException('Unknown subscribe mid', mid)

    def on_disconnect(self, client, userdata, rc):
        pass
        # print('>> disconnecting reason {}'.format(rc))
        
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
