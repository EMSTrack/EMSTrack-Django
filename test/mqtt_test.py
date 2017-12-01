import pytest

import sys, time
import json

from ambulances.management._client import BaseClient

# instead of settings
from eng100l.settings import MQTT

def compare_json(a, b):

    #print('a = {}, b = {}'.format(a, b))
    
    # lists
    if isinstance(a, list):

        # list of same size?
        if (not isinstance(b, list)) or len(a) != len(b):
            return False
            
        # iterate over sorted list
        for ia, ib in zip(sorted(a, key=lambda k: str(k)),
                          sorted(b, key=lambda k: str(k))):
            if not compare_json(ia, ib):
                return False
                
        # same list!
        return True

    # dict
    if isinstance(a, dict):

        # dict of same size?
        if (not isinstance (b, dict)) or len(a) != len(b):
            return False
            
        # iterate over dictionary keys
        for k, v in a.items():
            if not compare_json(v, b[k]):
                return False
                
        # same dict
        return True

    # simple value - compare both value and type for equality
    return a == b and type(a) is type(b)


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
            expect = self.expect_fifo[msg.topic].pop(0)
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
            assert compare_json(value, expect)

            print('< expectcount: {}'.format(self.expectcount))
            
        elif True: #False:
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
            self.expect_fifo[topic].append(msg)
        else:
            self.expect_fifo[topic] = [msg]
        self.expectcount += 1 

        print('> expectcount: {}'.format(self.expectcount))
        
    # user defined testing
    def test(self):
        print('WARNING: NO TESTING PERFORMED. YOU MUST OVERLOAD test')

def run_test(label, tests):

    print('\n* Testing {}'.format(label))

    style = Style()
    
    broker = {}
    broker.update(MQTT)
    broker.update({
        'USERNAME': 'testuser1',
        'PASSWORD': 'cruzrojauser1',
        'HOST': 'localhost',
        'PORT': 1883,
        'KEEPALIVE': 60,
        'CLIENT_ID': 'test',
        'CLEAN_SESSION': True
    })

    broker['CLIENT_ID'] = 'test' + label
    client = Client(broker, sys.stdout, style, verbosity = 1)

    try:
        
        client.loop_start()
        
        tests(client)
        
        while not client.done():
            time.sleep(1)
            
        client.loop_stop()
            
    except KeyboardInterrupt:
        pass
        
    finally:
        client.disconnect()

def hospital_login(client):

    # list of hospitals
    client.expect('user/testuser1/hospitals',
                  {"hospitals": [{"id":4,"name":"General Hospital"},
                                 {"id":5,"name":"Popular Insurance IMSS Clinic"}]})
    
    # login to hospital
    client.publish('user/testuser1/hospital', 4,
                 qos=2, retain=False)
    client.expect('user/testuser1/hospital', '4')
    
    # get hospital metadata
    client.expect('hospital/4/metadata',
                  {"equipment":[{"name":"Tomography","toggleable":True},{"name":"Blood laboratory","toggleable":True},{"name":"Ultrasound","toggleable":True},{"name":"Radiograph","toggleable":True}]})
    
    # get hospital equipment
    client.expect('hospital/4/equipment/Tomography', '3')
    client.expect('hospital/4/equipment/Blood laboratory', '2')
    client.expect('hospital/4/equipment/Ultrasound', '6')
    client.expect('hospital/4/equipment/Radiograph', '5')

    # modify equipment
    client.publish('hospital/4/equipment/Tomography', 1,
                   qos=2, retain=True)
    client.expect('hospital/4/equipment/Tomography', '1')

    # revert back
    client.publish('hospital/4/equipment/Tomography', 3,
                   qos=2, retain=True)
    client.expect('hospital/4/equipment/Tomography', '3')
    
    client.publish('user/testuser1/hospital', -1,
                   qos=2,
                   retain=False)
    
    client.expect('user/testuser1/hospital', '-1')

def ambulance_login(client):
    
    # list of ambulances
    client.expect('user/testuser1/ambulances',
                  {"ambulances":[{"id":12,"license_plate":"BC-179"},{"id":11,"license_plate":"BC-160"},{"id":10,"license_plate":"BC-183"}]})
    
    # login to ambulance
    client.publish('user/testuser1/ambulance', 12,
                 qos=2, retain=False)
    client.expect('user/testuser1/ambulance', '12')
    
    # publish location
    client.publish('user/testuser1/location',
                 '{"location":{"latitude":32.41902124227067,"longitude":-116.9496227294922},"timestamp": "2019-11-9 14:31:59"}',
                 qos=2, retain=True)
    client.expect('ambulance/12/location',
                  {"location":{"latitude":32.41902124227067,"longitude": -116.9496227294922},"orientation":0.0})
    
    # logout
    client.publish('user/testuser1/ambulance', -1,
                 qos=2,
                 retain=False)
    
    client.expect('user/testuser1/ambulance', '-1')
    
def test1():

    run_test('hospital_login', hospital_login)

def test2():

    run_test('ambulance_login', ambulance_login)
    
if __name__ == '__main__':

    test1()    
