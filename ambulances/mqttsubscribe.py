from django.contrib.auth.models import User

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from ambulances.mqttclient import BaseClient, MQTTException

from ambulances.models import Ambulance, Hospital, HospitalEquipment

from ambulances.serializers import AmbulanceSerializer, \
    HospitalSerializer, HospitalEquipmentSerializer

# SubscribeClient
class SubscribeClient(BaseClient):

    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        # Subscribing in on_connect() means that if we lose the
        # connection and reconnect then subscriptions will be renewed.
        # client.subscribe('#', 2)

        # ambulance handler
        self.client.message_callback_add('user/+/ambulance/+/data',
                                         self.on_ambulance)
        
        # hospital handler
        self.client.message_callback_add('user/+/hospital/+/data',
                                         self.on_hospital)

        # hospital equipment handler
        self.client.message_callback_add('hospital/+/equipment/+/data',
                                         self.on_hospital_equipment)
        
        # call handler
        #self.client.message_callback_add('ambulance/+/call',
        #                                 self.on_call)

        # subscribe
        self.subscribe('user/+/ambulance/+/data', 2)
        self.subscribe('user/+/hospital/+/data', 2)
        self.subscribe('user/+/hospital/+/equipment/+/data', 2)
        
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Listening to MQTT messages..."))

        return True

    def parse_topic(self, msg):

        if not msg.payload:
            # empty payload
            return
        
        # parse topic
        values = msg.topic.split('/')

        try:

            # retrieve user
            user = User.objects.get(username=values[1])

        except ObjectDoesNotExist:
            
            # TODO: send message to user
            pass
            
        # parse data
        try:
            
            # Parse data into json dict
            data = JSONParser().parse(BytesIO(msg.payload))
            
        except Exception as e:

            # TODO: send message to user
            print(e)
            self.stdout.write(
                self.style.ERROR("*> JSON formatted incorrectly: {}:{}".format(msg.topic, msg.payload)))
            return

        if len(values) == 5:
            return (user, data, values[3])
    
        elif len(values) == 7:
            
            return (user, data, values[3], values[5])
        
    # Update ambulance
    def on_ambulance(self, client, userdata, msg):

        # parse topic
        user, data, ambulance_id = self.parse_topic(msg)

        try:

            # retrieve ambulance
            ambulance = Ambulance.objects.get(id=ambulance_id)

        except ObjectDoesNotExist:

            # TODO: send message to user
            self.stdout.write(
                self.style.ERROR("*> Ambulance with id {} does not exist".format(ambulance_id)))
            return
            
        # update ambulance
        serializer = AmbulanceSerializer(ambulance,
                                         data=data,
                                         partial=True)
        if serializer.is_valid():

            # save to database
            serializer.save(updated_by=user)

        else:
            
            # TODO: send message to user
            pass
            
    # Update hospital
    def on_hospital(self, client, userdata, msg):

        # parse topic
        user, data, hospital_id = self.parse_topic(msg)

        try:

            # retrieve hospital
            hospital = Hospital.objects.get(id=hospital_id)

        except ObjectDoesNotExist:

            # TODO: send message to user
            self.stdout.write(
                self.style.ERROR("*> Hospital with id {} does not exist".format(hospital_id)))
            return
            
        # update hospital
        serializer = HospitalSerializer(hospital,
                                        data=data,
                                        partial=True)
        if serializer.is_valid():

            # save to database
            serializer.save(updated_by=user)

        else:
            
            # TODO: send message to user
            pass

    # Update hospital equipment
    def on_hospital_equipment(self, client, userdata, msg):

        # parse topic
        user, data, hospital_id, equipment_name = self.parse_topic(msg)

        try:

            # retrieve hospital equipment
            hospital_equipment = HospitalEquipment.objects.get(hospital=hospital_id,
                                                               equipment__name=equipment_name)

        except ObjectDoesNotExist:

            # TODO: send message to user
            self.stdout.write(
                self.style.ERROR("*> Hospital equipment with id {} and {} does not exist".format(hospital_id, equipment_name)))
            return
            
        # update hospital equipment
        serializer = HospitalEquipmentSerializer(hospital_equipment,
                                                 data=data,
                                                 partial=True)
        if serializer.is_valid():
            
            # save to database
            serializer.save(updated_by=user)
            
        else:
            
            # TODO: send message to user
            pass
