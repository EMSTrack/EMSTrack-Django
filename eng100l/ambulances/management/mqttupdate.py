
from ambulances.management._client import BaseClient

from ambulances.models import Ambulances, User, Equipment, EquipmentCount, Hospital
from ambulances.serializers import MQTTAmbulanceLocSerializer, MQTTAmbulanceListSerializer, MQTTHospitalEquipmentSerializer, MQTTHospitalListSerializer

from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

class UpdateClient(BaseClient):

    def publish(self, topic, message, *vargs, **kwargs):
        # increment pubcount then publish
        self.client.publish(topic, message, *vargs, **kwargs)

    def create_ambulance(self, obj):

        # Publish to new location topic
        serializer = MQTTAmbulanceLocSerializer(obj)
        json = JSONRenderer().render(serializer.data)
        self.publish('ambulance/{}/location'.format(obj.id), json, qos=2, retain=True)

        # Publish to new status topic
        self.publish('ambulance/{}/status'.format(obj.id), obj.status.name, qos=2, retain=True)

    def edit_ambulance(self, obj):
        # Publish new ambulance lists for all users
        for user in User.objects.filter(ambulances=obj.id):
            serializer = MQTTAmbulanceListSerializer(user)
            json = JSONRenderer().render(serializer.data)
            self.publish('user/{}/ambulances'.format(user.username), json, qos=2, retain=True)

        # Publish to new status topic
        self.publish('ambulance/{}/status'.format(obj.id), obj.status.name, qos=2, retain=True)

    def create_hospital(self, obj):
        # Publish config file for hospital
        serializer = MQTTHospitalEquipmentSerializer(obj)
        json = JSONRenderer().render(serializer.data)
        self.publish('hospital/{}/metadata'.format(obj.id), json, qos=2, retain=True)

    def edit_hospital(self, obj):
        # Publish new hospital lists for all users
        for user in User.objects.filter(hospitals=obj.id):
            serializer = MQTTHospitalListSerializer(user)
            json = JSONRenderer().render(serializer.data)
            self.publish('user/{}/hospitals'.format(user.username), json, qos=2, retain=True)

    def create_equipment(self, obj):
        # don't do anything
        return

    def edit_equipment(self, obj):
        # Publish hospital configurations for hospitals that contain the edited equipment
        hospitals = []

        # Find all the hospitals that have the edited equipment
        # Create new topics for the edited equipment
        for equipmentCount in EquipmentCount.objects.filter(equipment=obj.id):
            hospital = equipmentCount.hospital
            hospitals.append(hospital)
            self.publish('hospital/{}/equipment/{}'.format(hospital.id,
                                                                equipmentCount.equipment),
                            equipmentCount.quantity,
                            qos=2,
                            retain=True)

        for h in hospitals:
            serializer = MQTTHospitalEquipmentSerializer(h)
            json = JSONRenderer().render(serializer.data)
            self.publish('hospital/{}/metadata'.format(h.id), json, qos=2, retain=True)

    def create_equipment_count(self, obj):
        # Publish new equipment count topic
        hospital = obj.hospital
        print('hospital/{}/equipment/{}'.format(hospital.id, obj.equipment))
        self.publish('hospital/{}/equipment/{}'.format(hospital.id,
                                                            obj.equipment),
                        obj.quantity,
                        qos=2,
                        retain=True)

        # Update the hospital configuration topics to account for the new/edited equipment
        serializer = MQTTHospitalEquipmentSerializer(hospital)
        json = JSONRenderer().render(serializer.data)
        self.publish('hospital/{}/metadata'.format(hospital.id), json, qos=2, retain=True)

    def edit_equipment_count(self, obj):
        # Editing EquipmentCount value is the same as creating a new EquipmentCount
        self.create_equipment_count(obj)

    def create_user(self, obj):
        self.create_user_ambulance_list(obj)
        self.create_user_hospital_list(obj)

    def create_user_hospital_list(self, obj):
        # Publish hospital access list
        serializer = MQTTHospitalListSerializer(obj)
        json = JSONRenderer().render(serializer.data)
        self.publish('user/{}/hospitals'.format(obj.username), json, qos=2, retain=True)

    def create_user_ambulance_list(self, obj):
        # Publish ambulance access list
        serializer = MQTTAmbulanceListSerializer(obj)
        json = JSONRenderer().render(serializer.data)
        self.publish('user/{}/ambulances'.format(obj.username), json, qos=2, retain=True)

    def edit_user_hospital_list(self, obj):
        # Editing user does the same thing that create user does
        self.create_user_hospital_list(obj)

    def edit_user_ambulance_list(self, obj):
        self.create_user_ambulance_list(obj)
