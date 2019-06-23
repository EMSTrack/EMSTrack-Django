from django.test import Client

from django.conf import settings

from rest_framework.parsers import JSONParser
from io import BytesIO

from ambulance.models import Location, LocationType
from ambulance.serializers import LocationSerializer

from emstrack.tests.util import date2iso, point2str, dict2point

from login.tests.setup_data import TestSetup


class TestLocationGetList(TestSetup):

    def test_location_serializer(self):
        # test LocationSerializer
        for h in (self.l1, self.l2, self.l3):
            serializer = LocationSerializer(h)
            result = {
                'id': h.id,
                'name': h.name,
                'type': h.type,
                'number': h.number,
                'street': h.street,
                'unit': h.unit,
                'neighborhood': h.neighborhood,
                'city': h.city,
                'state': h.state,
                'zipcode': h.zipcode,
                'country': h.country,
                'location': point2str(h.location),
                'comment': h.comment,
                'updated_by': h.updated_by.id,
                'updated_on': date2iso(h.updated_on)
            }
            self.assertDictEqual(serializer.data, result)

    def test_location_serializer_create(self):
        
        # test LocationSerializer create
        json = {
            'type': LocationType.i.name,
            'number': '123',
            'street': 'some street'
        }
        serializer = LocationSerializer(data=json)
        serializer.is_valid()
        loc = serializer.save(updated_by=self.u1)

        # test CallSerializer
        l1 = Location.objects.get(id=loc.id)
        serializer = LocationSerializer(l1)

        expected = {
            'id': l1.id,
            'name': l1.name,
            'type': l1.type,
            'number': '123',
            'street': 'some street',
            'unit': l1.unit,
            'neighborhood': l1.neighborhood,
            'city': l1.city,
            'state': l1.state,
            'zipcode': l1.zipcode,
            'country': l1.country,
            'location': point2str(l1.location),
            'comment': l1.comment,
            'updated_by': l1.updated_by.id,
            'updated_on': date2iso(l1.updated_on)
        }
        result = serializer.data
        self.assertEqual(result, expected)
        
        json = {
            'type': LocationType.w.name,
            'location': {
                'longitude': -110.54,
                'latitude': 35.75
            }
        }

        serializer = LocationSerializer(data=json)
        serializer.is_valid()
        loc = serializer.save(updated_by=self.u1)

        # test CallSerializer
        l2 = Location.objects.get(id=loc.id)
        serializer = LocationSerializer(l2)

        expected = {
            'id': l2.id,
            'name': l2.name,
            'type': l2.type,
            'number': l2.number,
            'street': l2.street,
            'unit': l2.unit,
            'neighborhood': l2.neighborhood,
            'city': l2.city,
            'state': l2.state,
            'zipcode': l2.zipcode,
            'country': l2.country,
            'location': {'longitude': -110.54, 'latitude': 35.75},
            'comment': l2.comment,
            'updated_by': l2.updated_by.id,
            'updated_on': date2iso(l2.updated_on)
        }
        result = serializer.data
        self.assertEqual(result, expected)

    def test_location_get_list_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve locations
        response = client.get('/en/api/location/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l1).data,
                  LocationSerializer(self.l2).data,
                  LocationSerializer(self.l3).data]
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve locations
        response = client.get('/en/api/location/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l1).data,
                  LocationSerializer(self.l2).data,
                  LocationSerializer(self.l3).data]
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve locations
        response = client.get('/en/api/location/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l1).data,
                  LocationSerializer(self.l2).data,
                  LocationSerializer(self.l3).data]
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

    def test_location_get_viewset_by_type(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve locations
        response = client.get('/en/api/location/a/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l1).data,
                  LocationSerializer(self.l3).data]
        self.assertCountEqual(result, answer)

        response = client.get('/en/api/location/b/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l2).data]
        self.assertCountEqual(result, answer)

        response = client.get('/en/api/location/o/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = []
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve locations
        response = client.get('/en/api/location/a/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l1).data,
                  LocationSerializer(self.l3).data]
        self.assertCountEqual(result, answer)

        response = client.get('/en/api/location/b/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l2).data]
        self.assertCountEqual(result, answer)

        response = client.get('/en/api/location/o/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = []
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve locations
        response = client.get('/en/api/location/a/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l1).data,
                  LocationSerializer(self.l3).data]
        self.assertCountEqual(result, answer)

        response = client.get('/en/api/location/b/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [LocationSerializer(self.l2).data]
        self.assertCountEqual(result, answer)

        response = client.get('/en/api/location/o/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = []
        self.assertCountEqual(result, answer)

        # logout
        client.logout()
