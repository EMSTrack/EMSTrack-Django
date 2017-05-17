import time
import paho.mqtt.client as mqtt

from django.core.management.base import BaseCommand
from ambulances.models import Hospital, EquipmentCount, Equipment

class BaseClient():
    
    # initialize client
    def __init__(self,
                 broker,
                 stdout,
                 style):
        
        # initialize client
        self.stdout = stdout
        self.style = style
        self.broker = broker

        self.stdout.write("Broker settings = {}".format(broker))
        
        if self.broker.CLIENT_ID:
            self.client = mqtt.Client(self.broker.CLIENT_ID,
                                      self.broker.CLEAN_SESSION)
        else:
            self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        
        # default message handler
        self.client.on_message = self.on_message

        if self.broker.USERNAME and self.broker.PASSWORD:
            self.client.username_pw_set(self.broker.USERNAME,
                                        self.broker.PASSWORD)
            
        self.client.connect(self.broker.HOST,
                            self.broker.PORT,
                            self.broker.KEEPALIVE)

        # populated?
        self.populated = False

    def on_connect(self, client, userdata, flags, rc):
        
        if rc:
            self.stdout.write(
                self.style.ERROR("Could not connect to brocker. Return code '" + str(rc) + "'"))
            return False

        # success!
        self.stdout.write(self.style.SUCCESS("Connected to the mqtt brocker"))

        return True

    # disconnect
    def disconnect(self):
        self.client.disconnect()
        
    # loop forever
    def loop_forever(self):
        self.client.loop_forever()

# Client
        
class Client(BaseClient):
        
    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        if not super().on_connect(client, userdata, flags, rc):
            return False
        
        # populate messages
        if not self.populated:

            # initialize hospitals
            self.stdout.write("Initializing hospitals")
            hospitals = Hospital.objects.all()
            k = 0
            for h in hospitals:
                k = k + 1
                self.stdout.write(" {:2d}. {}".format(k, h))
                equipment = EquipmentCount.objects.filter(hospital = h)
                for e in equipment:
                    self.stdout.write("     {}: {}".format(e.equipment,
                                                           e.quantity))
                    # publish message
                    client.publish('hospital/{}/equipment/{}'.format(h.id,
                                                                     e.equipment),
                                   e.quantity,
                                   qos=2,
                                   retain=True)

            self.stdout.write(
                self.style.SUCCESS("Done initializing hospitals"))

            self.populated = True
            
        # Subscribing in on_connect() means that if we lose the
        # connection and reconnect then subscriptions will be renewed.
        client.subscribe('#', 2)

        # hospital message handler
        self.client.message_callback_add('hospital/+/#',
                                         self.on_hospital)
        
        self.stdout.write(self.style.SUCCESS("Listening to messages..."))

        return True
        
    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):

        # handle unknown messages
        self.stdout.write(
            self.style.WARNING(
                "Unknown message topic {} {}".format(msg.topic,
                                                     msg.payload)))

    # Update hospital resources
    def on_hospital(self, client, userdata, msg):

        # parse message
        topic = msg.topic.split('/')
        hospital = topic[1]
        equipment = topic[3]

        if not msg.payload:
            return
        
        quantity = int(msg.payload)

        self.stdout.write("on_hospital: {} {}".format(msg.topic, quantity))

        try:
            
            e = EquipmentCount.objects.get(hospital = hospital,
                                           equipment__name = equipment)

            # update quantity
            if e.quantity != quantity:
                e.quantity = quantity
                e.save()
                self.stdout.write(
                    self.style.SUCCESS("Hospital '{}' equipment '{}' updated to '{}'".format(e.hospital.name, equipment, quantity)))

        except:
            
            self.stdout.write(
                self.style.ERROR("hospital/{}/equipment/{} is not available".format(hospital, equipment)))
                
if __name__ == "__main__":
    
    class style:

        def add_cr(self,x):
            return x + '\n'
        
        SUCCESS = add_cr
        ERROR = add_cr
        WARNING = add_cr
    
    import sys
    client = Client('brian', 'cruzroja', sys.stdout, style())

    try:
        client.loop_forever()

    except KeyboardInterrupt:
        pass

    finally:
        client.disconnect()
