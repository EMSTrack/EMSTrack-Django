import json
from io import BytesIO

from rest_framework.parsers import JSONParser

from django.conf import settings
from django.test import Client

from equipment.models import Equipment, EquipmentItem
from equipment.serializers import EquipmentItemSerializer, EquipmentSerializer
from emstrack.tests.util import date2iso
from login.tests.setup_data import TestSetup


class TestEquipmentItemGetList(TestSetup):

    def test_equipment_item_serializer(self):
        # test HospitalSerializer
        for he in (self.he1, self.he2, self.he3, self.he4):
            serializer = EquipmentItemSerializer(he)
            result = {
                'hospital_id': he.hospital.id,
                # 'hospital_name': he.hospital.name,
                'equipment_id': he.equipment.id,
                'equipment_name': he.equipment.name,
                'equipment_type': he.equipment.type,
                'value': he.value,
                'comment': he.comment,
                'updated_by': he.updated_by.id,
                'updated_on': date2iso(he.updated_on)
            }
            self.assertDictEqual(serializer.data, result)

    def test_equipment_item_get_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e2.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e3.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h3.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve inexistent
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e2.id)).data
        self.assertDictEqual(result, answer)

        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e3.id)).data
        self.assertDictEqual(result, answer)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()

    def test_equipment_item_list_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e1.id)).data,
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e2.id)).data
        ]

        self.assertCountEqual(result, answer)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e1.id)).data,
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e3.id)).data
        ]
        self.assertCountEqual(result, answer)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h3.id, equipment=self.e1.id)).data
        ]
        self.assertCountEqual(result, answer)

        # retrieve inexistent
        response = client.get('/api/hospital/{}/equipment/'.format(1000),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e1.id)).data,
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e2.id)).data
        ]

        self.assertCountEqual(result, answer)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e1.id)).data,
            EquipmentItemSerializer(EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e3.id)).data
        ]
        self.assertCountEqual(result, answer)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()


class TestEquipmentItemUpdate(TestSetup):

    def test_equipment_item_update_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # set equipment value
        value = 'True'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'value': value
                                })
                                )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve equipment value
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)

        # set equipment comment
        comment = 'some comment'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'comment': comment
                                })
                                )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h1.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve equipment comment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)
        self.assertEqual(result['comment'], comment)

        # set inexistent equipment
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e3.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'comment': comment
                                })
                                )
        self.assertEqual(response.status_code, 404)

        # set wrong ambulance id
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id + 100), str(self.e1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'comment': comment
                                })
                                )
        self.assertEqual(response.status_code, 403)

        # set wrong equipment name
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), -1),
                                content_type='application/json',
                                data=json.dumps({
                                    'comment': comment
                                })
                                )
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # set equipment value
        value = 'False'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'value': value
                                })
                                )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve equipment value
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)

        # set equipment comment
        comment = 'some new comment'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'comment': comment
                                })
                                )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = EquipmentItemSerializer(
            EquipmentItem.objects.get(hospital=self.h2.id, equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve equipment comment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)
        self.assertEqual(result['comment'], comment)

        # not permitted to write
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'value': value
                                })
                                )
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # set equipment value
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'value': value
                                })
                                )
        self.assertEqual(response.status_code, 403)

        # set equipment value
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'value': value
                                })
                                )
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()


class TestEquipmentMetadata(TestSetup):

    def test_equipment_metadata_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e2.id)).data
        ]
        self.assertCountEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e3.id)).data
        ]
        self.assertCountEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data
        ]
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e2.id)).data
        ]
        self.assertCountEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e3.id)).data
        ]
        self.assertCountEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()