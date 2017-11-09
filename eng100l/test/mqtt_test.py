import pytest

import sys, time
import json

from ambulances.management._client import BaseClient

# instead of settings
from eng100l.settings import MQTT

class Style():

    def ERROR(self, message):
        return "ERROR: " + message + "\n"
    
    def SUCCESS(self, message):
        return message + "\n"

# Client
class Client(BaseClient):

    def __init__(self, *args, **kwargs):

        # call supper
        super().__init__(*args, **kwargs)

        self.expect_fifo = {}

        # initialize pubcount
        self.pubcount = 0

        # initialize expectcount
        self.expectcount = 0

    def done(self):

        return self.pubcount == 0 and self.expectcount == 0
        
    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        # subscribe to everything
        client.subscribe('#', 2)
        
    # The callback for when a subscribed message is received from the server.
    def on_message(self, client, userdata, msg):

        if msg.topic in self.expect_fifo:

            # pop from expected list
            expect = self.expect_fifo[msg.topic].pop()
            value = msg.payload.decode()

            # remove topic if empty list
            if not self.expect_fifo[msg.topic]:
                del self.expect_fifo[msg.topic]

            # parse json
            if value and value[0] == '{' and value[-1] == '}':
                print('parse json')
                value = json.loads(value)
                
            print('> MATCH: {} {} == {}'.format(msg.topic, value, expect))

            self.expectcount -= 1
            assert expect == value
            
        elif False:
            print('* ignored message: {} {}'.format(msg.topic, msg.payload))

    def publish(self, topic, message, *vargs, **kwargs):
        # increment pubcount then publish
        self.pubcount += 1
        result, mid = self.client.publish(topic, message, *vargs, **kwargs)
        print('< Publishing [{}]: {} {}'.format(mid, topic, message))
        
    def on_publish(self, client, userdata, mid):
        # make sure all is published before disconnecting
        self.pubcount -= 1
        print('< Published: {}'.format(mid))
            
    def expect(self, topic, msg):
        print('> Expecting: {} {}'.format(topic, msg))
        if topic in self.expect_fifo:
            self.expect_fifo[topic].insert(0, msg)
        else:
            self.expect_fifo[topic] = [msg]
        self.expectcount += 1 

    # user defined testing
    def test(self):
        print('WARNING: NO TESTING PERFORMED. YOU MUST OVERLOAD test')

style = Style()
        
broker = {
    'HOST': 'localhost',
    'PORT': 1883,
    'KEEPALIVE': 60,
    'CLIENT_ID': 'test',
    'CLEAN_SESSION': False
}
broker.update(MQTT)

def run_test(client):

    print('\n* Testing {}'.format(type(client)))
    
    try:
        client.loop_start()
        
        client.test()
        
        while client.done():
            time.sleep(1)
            
        client.loop_stop()
            
    except KeyboardInterrupt:
        pass
        
    finally:
        client.disconnect()

def test1():

    class TestHospitalLogin(Client):

        def consume(self, topic):
            
            return self.topics.pop(topic).decode()

        def test(self):

            self.hospital_login()

            self.hospital_logout()
            
        def hospital_login(self):

            # list of hospitals
            client.expect('user/testuser1/hospitals',
                          {"hospitals": [{"id":4,"name":"General Hospital"},{"id":5,"name":"Popular Insurance IMSS Clinic"}]})
            
            # login to hospital
            self.publish('user/testuser1/hospital', 4,
                         qos=2, retain=False)
            client.expect('user/testuser1/hospital', '4')

            # get hospital metadata
            client.expect('hospital/4/metadata',
                          {"equipment":[{"name":"Tomography","toggleable":True},{"name":"Blood laboratory","toggleable":True},{"name":"Ultrasound","toggleable":True},{"name":"Radiograph","toggleable":True}]})

            # get hospital equipment
            client.expect('hospital/4/equipment/Tomography', '3')
            client.expect('hospital/4/equipment/Blood laboratory', '2')
            client.expect('hospital/4/equipment/Ultrasound', '6')
            client.expect('hospital/4/equipment/Radiography', '5')
            
        def hospital_logout(self):

            self.publish('user/testuser1/hospital', -1,
                         qos=2,
                         retain=False)

            client.expect('user/testuser1/hospital', '-1')
            
    client = TestHospitalLogin(broker, sys.stdout, style, verbosity = 1)

    run_test(client)

def test2():

    class TestHospitalEquipment(Client):

        def consume(self, topic):
            
            return self.topics.pop(topic).decode()

        def test(self):

            self.hospital_login()

            self.hospital_equipment()
            
            self.hospital_logout()
            
        def hospital_login(self):

            # list of hospitals
            client.expect('user/testuser1/hospitals',
                          {"hospitals":[{"id":4,"name":"General Hospital"},{"id":5,"name":"Popular Insurance IMSS Clinic"}]})
            
            # login to hospital
            self.publish('user/testuser1/hospital', 4,
                         qos=2, retain=False)
            client.expect('user/testuser1/hospital', '4')

            # get hospital metadata
            client.expect('hospital/4/metadata',
                          {"equipment":[{"name":"Tomography","toggleable":True},{"name":"Blood laboratory","toggleable":True},{"name":"Ultrasound","toggleable":True},{"name":"Radiograph","toggleable":True}]})

        def hospital_equipment(self):

            # modify equipment
            self.publish('hospital/4/equipment/Tomography', 1,
                         qos=2, retain=True)
            client.expect('hospital/4/equipment/Tomography', '1')

            # revert back
            self.publish('hospital/4/equipment/Tomography', 3,
                         qos=2, retain=True)
            client.expect('hospital/4/equipment/Tomography', '3')
            
        def hospital_logout(self):

            self.publish('user/testuser1/hospital', -1,
                         qos=2,
                         retain=False)

            client.expect('user/testuser1/hospital', '-1')
            
    client = TestHospitalEquipment(broker, sys.stdout, style, verbosity = 1)

    run_test(client)
    
if __name__ == '__main__':

    test1()    
