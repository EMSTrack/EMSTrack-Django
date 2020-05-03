import logging
import math

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.test import Client

from django.utils import timezone
from django.conf import settings

from rest_framework.parsers import JSONParser
from io import BytesIO
import json

from ambulance.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability, AmbulanceUpdate
from emstrack.latlon import calculate_orientation
from ambulance.serializers import AmbulanceSerializer, AmbulanceUpdateSerializer

from login.models import Client as loginClient

from emstrack.tests.util import date2iso, point2str, dict2point

from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestAmbulanceGetList(TestSetup):

    def test_ambulance_serializer(self):
        # test AmbulanceSerializer
        for a in (self.a1, self.a2, self.a3):
            serializer = AmbulanceSerializer(a)
            result = {
                'id': a.id,
                'identifier': a.identifier,
                'comment': a.comment,
                'capability': a.capability,
                'status': AmbulanceStatus.UK.name,
                'orientation': a.orientation,
                'location': point2str(a.location),
                'timestamp': date2iso(a.timestamp),
                'client_id': None,
                'updated_by': a.updated_by.id,
                'updated_on': date2iso(a.updated_on)
            }
            self.assertDictEqual(serializer.data, result)

    def test_ambulance_get_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve any ambulance
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any ambulance
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a2.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any ambulance
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a3.id)).data
        self.assertDictEqual(result, answer)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve own
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a3.id)).data
        self.assertDictEqual(result, answer)

        # retrieve someone else's
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # can't read
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve someone else's
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve someone else's
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

    def test_ambulance_get_list_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve ambulances
        response = client.get('/en/api/ambulance/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [AmbulanceSerializer(self.a1).data,
                  AmbulanceSerializer(self.a2).data,
                  AmbulanceSerializer(self.a3).data]
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve ambulances
        response = client.get('/en/api/ambulance/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = []
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve ambulances
        response = client.get('/en/api/ambulance/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [  # AmbulanceSerializer(self.a1).data, # can't read
            AmbulanceSerializer(Ambulance.objects.get(id=self.a3.id)).data]
        self.assertCountEqual(result, answer)

        # logout
        client.logout()


class TestAmbulanceUpdate(TestSetup):

    def test_ambulance_update_serializer(self):

        # superuser first

        # Update ambulance status
        a = self.a1
        user = self.u1
        status = AmbulanceStatus.AH.name

        serializer = AmbulanceSerializer(a,
                                         data={
                                             'status': status,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': status,
            'orientation': a.orientation,
            'location': point2str(a.location),
            'client_id': None,
            'timestamp': date2iso(a.timestamp),
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # Update ambulance location
        timestamp = timezone.now()
        location = {'latitude': -2., 'longitude': 7.}

        serializer = AmbulanceSerializer(a,
                                         data={
                                             'location': location,
                                             'timestamp': timestamp,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': a.status,
            'orientation': a.orientation,
            'location': point2str(location),
            'client_id': None,
            'timestamp': date2iso(timestamp),
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # error update timestamp without location or status
        serializer = AmbulanceSerializer(a,
                                         data={
                                             'timestamp': timestamp,
                                         }, partial=True)
        self.assertEqual(serializer.is_valid(), False)

        # regular authorized user

        # Update ambulance status
        a = self.a3
        user = self.u3
        status = AmbulanceStatus.AH.name

        serializer = AmbulanceSerializer(a,
                                         data={
                                             'status': status,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': status,
            'orientation': a.orientation,
            'location': point2str(a.location),
            'client_id': None,
            'timestamp': date2iso(a.timestamp),
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # Update ambulance location
        timestamp = timezone.now()
        location = {'latitude': -2., 'longitude': 7.}

        serializer = AmbulanceSerializer(a,
                                         data={
                                             'location': location,
                                             'timestamp': timestamp
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': a.status,
            'orientation': a.orientation,
            'location': point2str(location),
            'client_id': None,
            'timestamp': date2iso(timestamp),
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # error update timestamp without location or status
        serializer = AmbulanceSerializer(a,
                                         data={
                                             'timestamp': timestamp,
                                         }, partial=True)
        self.assertEqual(serializer.is_valid(), False)

        # update client
        client1 = loginClient(client_id='client_id_1', user_id=self.u1.id, ambulance=a)
        client1.save()

        client2 = loginClient(client_id='client_id_2', user_id=self.u3.id)
        client2.save()

        self.assertEqual(client1.ambulance, a)
        self.assertEqual(client2.ambulance, None)
        self.assertEqual(a.client, client1)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': a.status,
            'orientation': a.orientation,
            'location': point2str(location),
            'timestamp': date2iso(timestamp),
            'client_id': client1.client_id,
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # will not change
        client2.ambulance = self.a2
        with self.assertRaises(Exception) as raised:
            with transaction.atomic():
                client2.save()
        self.assertEqual(PermissionDenied, type(raised.exception))

        # will not change
        client2.ambulance = a
        with self.assertRaises(Exception) as raised:
            with transaction.atomic():
                client2.save()
        self.assertEqual(IntegrityError, type(raised.exception))

        client2 = loginClient.objects.get(client_id='client_id_2')
        a = Ambulance.objects.get(id=a.id)

        self.assertEqual(client1.ambulance, a)
        self.assertEqual(client2.ambulance, None)
        self.assertEqual(a.client, client1)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': a.status,
            'orientation': a.orientation,
            'location': point2str(location),
            'timestamp': date2iso(timestamp),
            'client_id': client1.client_id,
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # will reset
        client1.ambulance = None
        client1.save()
        a = Ambulance.objects.get(id=a.id)

        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client2.ambulance, None)
        self.assertEqual(hasattr(a, 'client'), False)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': a.status,
            'orientation': a.orientation,
            'location': point2str(location),
            'timestamp': date2iso(timestamp),
            'client_id': None,
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # will change
        client2.ambulance = a
        client2.save()

        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client2.ambulance, a)
        self.assertEqual(a.client, client2)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': a.status,
            'orientation': a.orientation,
            'location': point2str(location),
            'timestamp': date2iso(timestamp),
            'client_id': client2.client_id,
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # will not change in partial update
        serializer = AmbulanceSerializer(a,
                                         data={
                                             'status': AmbulanceStatus.OS.name
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': AmbulanceStatus.OS.name,
            'orientation': a.orientation,
            'location': point2str(location),
            'timestamp': date2iso(timestamp),
            'client_id': client2.client_id,
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # will not change in partial update
        serializer = AmbulanceSerializer(a,
                                         data={
                                             'status': AmbulanceStatus.PB.name,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': AmbulanceStatus.PB.name,
            'orientation': a.orientation,
            'location': point2str(location),
            'timestamp': date2iso(timestamp),
            'client_id': client2.client_id,
            'updated_by': user.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

    def test_ambulance_patch_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve ambulance
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(self.a1).data
        self.assertDictEqual(result, answer)

        # set status ambulance
        status = AmbulanceStatus.OS.name
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve new ambulance status
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                              follow = True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], status)

        # set status location
        timestamp = timezone.now()
        location = {'latitude': -2., 'longitude': 7.}

        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'location': point2str(location),
                                    'timestamp': date2iso(timestamp),
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a1.id)).data
        if math.fabs(answer['orientation'] - result['orientation']) < 1e-4:
            answer['orientation'] = result['orientation']
        self.assertDictEqual(result, answer)

        # retrieve new ambulance location
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a1.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], status)
        self.assertEqual(result['location'], point2str(location))
        self.assertEqual(result['timestamp'], date2iso(timestamp))

        # set wrong attribute
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': 'will fail'
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 400)

        # set wrong ambulance id
        response = client.patch('/en/api/ambulance/100/',
                                data=json.dumps({
                                    'status': status
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve ambulance
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(self.a3).data
        self.assertDictEqual(result, answer)

        # set status ambulance
        status = AmbulanceStatus.OS.name
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a3.id)).data
        self.assertDictEqual(result, answer)

        # retrieve new ambulance status
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], status)

        # set location
        timestamp = timezone.now()
        location = {'latitude': -2., 'longitude': 7.}

        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'location': point2str(location),
                                    'timestamp': date2iso(timestamp),
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a3.id)).data
        if math.fabs(answer['orientation'] - result['orientation']) < 1e-4:
            answer['orientation'] = result['orientation']
        self.assertDictEqual(result, answer)

        # retrieve new ambulance location
        response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], status)
        self.assertEqual(result['location'], point2str(location))
        self.assertEqual(result['timestamp'], date2iso(timestamp))

        # set status ambulance
        status = AmbulanceStatus.OS.name
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 404)

        # set status ambulance
        status = AmbulanceStatus.OS.name
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a2.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # set status ambulance
        status = AmbulanceStatus.OS.name
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 404)

        # set status ambulance
        status = AmbulanceStatus.OS.name
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a2.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 404)

        # set status ambulance
        status = AmbulanceStatus.OS.name
        response = client.patch('/en/api/ambulance/{}/'.format(str(self.a3.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()


class TestAmbulanceCreate(TestSetup):

    def test_ambulance_create_serializer(self):
        serializer = AmbulanceSerializer(data={
            'identifier': 'NEW-1897',
            'capability': AmbulanceCapability.R.name,
            'comment': 'no comments'
        })
        serializer.is_valid()
        serializer.save(updated_by=self.u1)

        # test AmbulanceSerializer
        a = Ambulance.objects.get(identifier='NEW-1897')
        serializer = AmbulanceSerializer(a)
        result = {
            'id': a.id,
            'identifier': 'NEW-1897',
            'comment': 'no comments',
            'capability': AmbulanceCapability.R.name,
            'status': AmbulanceStatus.UK.name,
            'orientation': a.orientation,
            'location': point2str(a.location),
            'timestamp': date2iso(a.timestamp),
            'client_id': None,
            'updated_by': self.u1.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

    def test_ambulance_post_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # create ambulance
        response = client.post('/en/api/ambulance/',
                               {
                                   'identifier': 'NEW-1897',
                                   'capability': AmbulanceCapability.R.name,
                                   'comment': 'no comments'
                               }
                               )
        self.assertEqual(response.status_code, 201)
        a = Ambulance.objects.get(identifier='NEW-1897')

        # retrieve ambulance
        response = client.get('/en/api/ambulance/{}/'.format(str(a.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(a).data
        self.assertDictEqual(result, answer)

        # create ambulance (repeated identifier)
        response = client.post('/en/api/ambulance/',
                               {
                                   'identifier': 'NEW-1897',
                                   'capability': AmbulanceCapability.R.name,
                                   'comment': 'no comments'
                               }
                               )
        self.assertEqual(response.status_code, 400)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['identifier'],
                         ['ambulance with this identifier already exists.'])

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        response = client.post('/en/api/ambulance/',
                               {
                                   'identifier': 'NEW-NEW-1897',
                                   'capability': AmbulanceCapability.B.name,
                                   'comment': 'more comments'
                               }
                               )
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        response = client.post('/en/api/ambulance/',
                               {
                                   'identifier': 'NEW-NEW-1897',
                                   'capability': AmbulanceCapability.B.name,
                                   'comment': 'more comments'
                               }
                               )
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()


class TestAmbulanceUpdates(TestSetup):

    def test(self):

        self.maxDiff = None

        # Update ambulance a1
        a = self.a1
        user = self.u1

        status = AmbulanceStatus.AH.name
        serializer = AmbulanceSerializer(Ambulance.objects.get(id=a.id),
                                         data={
                                             'status': status,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        timestamp = timezone.now()
        location = {'latitude': -2., 'longitude': 7.}

        serializer = AmbulanceSerializer(Ambulance.objects.get(id=a.id),
                                         data={
                                             'location': location,
                                             'timestamp': timestamp
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        status = AmbulanceStatus.OS.name
        serializer = AmbulanceSerializer(Ambulance.objects.get(id=a.id),
                                         data={
                                             'status': status,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # This update does not go to AmbulanceUpdate!
        serializer = AmbulanceSerializer(Ambulance.objects.get(id=a.id),
                                         data={
                                             'identifier': 'someid',
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test AmbulanceUpdateSerializer
        queryset = AmbulanceUpdate.objects.filter(ambulance=a)
        answer1 = []
        for u in queryset:
            serializer = AmbulanceUpdateSerializer(u)
            result = {
                'id': u.id,
                'ambulance_id': u.ambulance.id,
                'ambulance_identifier': u.ambulance.identifier,
                'comment': u.comment,
                'capability': u.capability,
                'status': u.status,
                'orientation': u.orientation,
                'location': point2str(u.location),
                'timestamp': date2iso(u.timestamp),
                'updated_by_username': u.updated_by.username,
                'updated_on': date2iso(u.updated_on)
            }
            answer1.append(serializer.data)
            self.assertDictEqual(serializer.data, result)

        # Update ambulance a2
        a = self.a3
        user = self.u3

        status = AmbulanceStatus.AH.name
        serializer = AmbulanceSerializer(a,
                                         data={
                                             'status': status,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        timestamp = timezone.now()
        location = {'latitude': -2., 'longitude': 7.}

        serializer = AmbulanceSerializer(a,
                                         data={
                                             'location': location,
                                             'timestamp': timestamp
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        status = AmbulanceStatus.OS.name
        serializer = AmbulanceSerializer(a,
                                         data={
                                             'status': status,
                                         }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test AmbulanceUpdateSerializer
        queryset = AmbulanceUpdate.objects.filter(ambulance=a)
        answer3 = []
        for u in queryset:
            serializer = AmbulanceUpdateSerializer(u)
            result = {
                'id': u.id,
                'ambulance_id': u.ambulance.id,
                'ambulance_identifier': a.identifier,
                'comment': u.comment,
                'capability': u.capability,
                'status': u.status,
                'orientation': u.orientation,
                'location': point2str(u.location),
                'timestamp': date2iso(u.timestamp),
                'updated_by_username': u.updated_by.username,
                'updated_on': date2iso(u.updated_on)
            }
            answer3.append(serializer.data)
            self.assertDictEqual(serializer.data, result)

        # Test api

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve ambulances updates
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(result), 4)
        self.assertCountEqual(result, answer1)

        # retrieve ambulances updates
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(result), 4)
        self.assertCountEqual(result, answer3)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve ambulances
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve ambulances
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve ambulances
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve ambulances updates
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertCountEqual(result, answer3)
        self.assertEqual(len(result), 4)

        # logout
        client.logout()


class TestAmbulanceBulkUpdates(TestSetup):

    def test(self):

        self.maxDiff = None

        # Bulk update ambulance a1
        a = self.a1
        user = self.u1

        location0 = {'latitude': -3., 'longitude': 6.}
        location = {'latitude': -2., 'longitude': 7.}
        orientation = calculate_orientation(dict2point(location0), dict2point(location))
        data = [
            {
                'status': AmbulanceStatus.AH.name,
                'location': location0,
            },
            {
                'location': location,
                'timestamp': timezone.now()
            },
            {'status': AmbulanceStatus.OS.name}
        ]

        serializer = AmbulanceUpdateSerializer(data=data, many=True, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(ambulance=Ambulance.objects.get(id=a.id),
                        updated_by=user)

        # test AmbulanceUpdateSerializer
        queryset = AmbulanceUpdate.objects.filter(ambulance=a)
        answer1 = []
        for u in queryset:
            serializer = AmbulanceUpdateSerializer(u)
            result = {
                'id': u.id,
                'ambulance_id': u.ambulance.id,
                'ambulance_identifier': u.ambulance.identifier,
                'comment': u.comment,
                'capability': u.capability,
                'status': u.status,
                'orientation': u.orientation,
                'location': point2str(u.location),
                'timestamp': date2iso(u.timestamp),
                'updated_by_username': u.updated_by.username,
                'updated_on': date2iso(u.updated_on)
            }
            answer1.append(serializer.data)
            self.assertDictEqual(serializer.data, result)

        # make sure last update is reflected in ambulance
        a = Ambulance.objects.get(id=a.id)
        serializer = AmbulanceSerializer(a)
        self.assertEqual(math.fabs(orientation - a.orientation) < 1e-4, True)
        orientation = a.orientation
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': AmbulanceStatus.OS.name,
            'orientation': orientation,
            'location': point2str(location),
            'timestamp': date2iso(a.timestamp),
            'client_id': None,
            'updated_by': a.updated_by.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # Bulk update ambulance a2
        a = self.a3
        user = self.u3

        data = [
            {
                'status': AmbulanceStatus.AH.name,
                'location': location0
            },
            {'status': AmbulanceStatus.OS.name},
            {
                'location': location,
                'timestamp': timezone.now()
            }
        ]

        serializer = AmbulanceUpdateSerializer(data=data, many=True, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(ambulance=Ambulance.objects.get(id=a.id),
                        updated_by=user)

        # test AmbulanceUpdateSerializer
        queryset = AmbulanceUpdate.objects.filter(ambulance=a)
        answer3 = []
        for u in queryset:
            serializer = AmbulanceUpdateSerializer(u)
            result = {
                'id': u.id,
                'ambulance_id': a.id,
                'ambulance_identifier': a.identifier,
                'comment': u.comment,
                'capability': u.capability,
                'status': u.status,
                'orientation': u.orientation,
                'location': point2str(u.location),
                'timestamp': date2iso(u.timestamp),
                'updated_by_username': u.updated_by.username,
                'updated_on': date2iso(u.updated_on)
            }
            answer3.append(serializer.data)
            self.assertDictEqual(serializer.data, result)

        # make sure last update is reflected in ambulance
        a = Ambulance.objects.get(id=a.id)
        serializer = AmbulanceSerializer(a)
        self.assertEqual(math.fabs(orientation - a.orientation) < 1e-4, True)
        orientation = a.orientation
        result = {
            'id': a.id,
            'identifier': a.identifier,
            'comment': a.comment,
            'capability': a.capability,
            'status': AmbulanceStatus.OS.name,
            'orientation': orientation,
            'location': point2str(location),
            'timestamp': date2iso(a.timestamp),
            'client_id': None,
            'updated_by': a.updated_by.id,
            'updated_on': date2iso(a.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # Test api

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve ambulances updates
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(result), 4)
        self.assertCountEqual(result, answer1)

        # retrieve ambulances updates
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertCountEqual(result, answer3)
        self.assertEqual(len(result), 4)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve ambulances
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve ambulances
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve ambulances
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve ambulances updates
        response = client.get('/en/api/ambulance/{}/updates/'.format(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertCountEqual(result, answer3)
        self.assertEqual(len(result), 4)

        # logout
        client.logout()

