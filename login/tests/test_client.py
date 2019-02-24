import json
import logging
from io import BytesIO

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from rest_framework.parsers import JSONParser
from django.test import Client as DjangoClient

from ambulance.models import Ambulance
from emstrack.tests.util import date2iso
from hospital.models import Hospital
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from login.serializers import ClientSerializer
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestClient(TestSetup):

    def testAmbulance(self):

        # client online
        client1 = Client.objects.create(client_id='client_id_1', user=self.u1,
                                        status=ClientStatus.O.name)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 1)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 2)

        # go online with ambulance
        client1.status = ClientStatus.O.name
        client1.ambulance = self.a1
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a1)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a1.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 4)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.AO.name)
        self.assertEqual(log.details, self.a1.identifier)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 6)

        # client online
        client1.status = ClientStatus.O.name
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 7)

        # login ambulance a1
        client1.ambulance = self.a1
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a1)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a1.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 9)

        # logout ambulance
        client1.ambulance = None
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AO.name)
        self.assertEqual(log.details, self.a1.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 11)

        # login ambulance a2
        client1.ambulance = self.a2
        client1.save()

        a = Ambulance.objects.get(id=self.a2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a2)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a2.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 13)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        a = Ambulance.objects.get(id=self.a2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.AO.name)
        self.assertEqual(log.details, self.a2.identifier)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 15)

    def testHospital(self):

        # client online
        client1 = Client.objects.create(client_id='client_id_1', user=self.u1,
                                        status=ClientStatus.O.name)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 1)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 2)

        # go online with hospital
        client1.status = ClientStatus.O.name
        client1.hospital = self.h1
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.hospital, self.h1)
        self.assertEqual(h.client, client1)
        self.assertEqual(client1.ambulance, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HI.name)
        self.assertEqual(log.details, self.h1.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 4)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(h, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HO.name)
        self.assertEqual(log.details, self.h1.name)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 6)

        # client online
        client1.status = ClientStatus.O.name
        client1.save()

        h = Ambulance.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 7)

        # login hospital a1
        client1.hospital = self.h1
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.hospital, self.h1)
        self.assertEqual(h.client, client1)
        self.assertEqual(client1.ambulance, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HI.name)
        self.assertEqual(log.details, self.h1.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 9)

        # logout ambulance
        client1.hospital = None
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(h, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HO.name)
        self.assertEqual(log.details, self.h1.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 11)

        # login ambulance a2
        client1.hospital = self.h2
        client1.save()

        h = Hospital.objects.get(id=self.h2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.hospital, self.h2)
        self.assertEqual(h.client, client1)
        self.assertEqual(client1.ambulance, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HI.name)
        self.assertEqual(log.details, self.h2.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 13)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        h = Hospital.objects.get(id=self.h2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(h, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HO.name)
        self.assertEqual(log.details, self.h2.name)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 15)

    def testPermissions(self):

        with self.assertRaises(PermissionDenied):
            with transaction.atomic():
                Client.objects.create(client_id='client_id_1', user=self.u2,
                                      status=ClientStatus.O.name, ambulance=self.a1)

        with self.assertRaises(PermissionDenied):
            with transaction.atomic():
                Client.objects.create(client_id='client_id_1', user=self.u2,
                                      status=ClientStatus.O.name, ambulance=self.a1, hospital=self.h1)

        with self.assertRaises(PermissionDenied):
            with transaction.atomic():
                Client.objects.create(client_id='client_id_1', user=self.u3,
                                      status=ClientStatus.O.name, hospital=self.h1)

        with self.assertRaises(PermissionDenied):
            with transaction.atomic():
                Client.objects.create(client_id='client_id_1', user=self.u3,
                                      status=ClientStatus.O.name, ambulance=self.a1, hospital=self.h1)

    def testClientSerializer(self):

        # test ClientSerializer

        # client online
        client1 = Client.objects.create(client_id='client_id_1', user=self.u1,
                                        status=ClientStatus.O.name, ambulance=self.a1)

        serializer = ClientSerializer(client1)
        result = {
            'id': client1.id,
            'client_id': client1.client_id,
            'user': client1.user.id,
            'status': client1.status,
            'ambulance': client1.ambulance.id,
            'hospital': None,
            'updated_on': date2iso(client1.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # create client
        serializer = ClientSerializer(data={
            'client_id': 'client_id_3',
            'status': ClientStatus.O.name,
            'ambulance': None,
            'hospital': None
        })
        if not serializer.is_valid():
            logger.debug('errors = {}'.format(serializer.errors))
            self.assertTrue(False)
        serializer.save(user=self.u2)

        client2 = Client.objects.get(client_id='client_id_3')

        self.assertEqual(client2.status, ClientStatus.O.name)
        self.assertEqual(client2.user, self.u2)
        self.assertEqual(client2.ambulance, None)
        self.assertEqual(client2.hospital, None)

        # create client
        serializer = ClientSerializer(data={
            'client_id': 'client_id_4',
            'status': ClientStatus.O.name,
            'ambulance': self.a2.id,
            'hospital': None
        })
        if not serializer.is_valid():
            logger.debug('errors = {}'.format(serializer.errors))
            self.assertTrue(False)
        serializer.save(user=self.u1)

        client2 = Client.objects.get(client_id='client_id_4')

        self.assertEqual(client2.status, ClientStatus.O.name)
        self.assertEqual(client2.user, self.u1)
        self.assertEqual(client2.ambulance, self.a2)
        self.assertEqual(client2.hospital, None)

        # update client
        serializer = ClientSerializer(data={
            'client_id': 'client_id_4',
            'hospital': self.h1.id
        }, partial=True)
        if not serializer.is_valid():
            logger.debug('errors = {}'.format(serializer.errors))
            self.assertTrue(False)
        serializer.save(user=self.u1)

        client2 = Client.objects.get(client_id='client_id_4')

        self.assertEqual(client2.status, ClientStatus.O.name)
        self.assertEqual(client2.user, self.u1)
        self.assertEqual(client2.ambulance, self.a2)
        self.assertEqual(client2.hospital, self.h1)

    def test_client_viewset(self):

        # instantiate client
        client = DjangoClient()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # create client online
        client1 = Client.objects.create(client_id='client_id_1', user=self.u2,
                                        status=ClientStatus.O.name)

        # retrieve
        response = client.get('/en/api/client/{}/'.format(str(client1.client_id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ClientSerializer(client1).data
        self.assertDictEqual(result, answer)
        self.assertEqual(result['user'], self.u2.id)

        # set status and ambulance
        status = ClientStatus.O.name
        response = client.patch('/en/api/client/{}/'.format(str(client1.client_id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': status,
                                    'ambulance': self.a1.id,
                                    'hospital': self.h1.id
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ClientSerializer(Client.objects.get(id=client1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve new status
        response = client.get('/en/api/client/{}/'.format(str(client1.client_id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], status)
        self.assertEqual(result['ambulance'], self.a1.id)
        self.assertEqual(result['hospital'], self.h1.id)
        self.assertEqual(result['user'], self.u1.id)

        # reset ambulance
        response = client.patch('/en/api/client/{}/'.format(str(client1.client_id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'ambulance': None
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ClientSerializer(Client.objects.get(id=client1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve new status
        response = client.get('/en/api/client/{}/'.format(str(client1.client_id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], status)
        self.assertEqual(result['ambulance'], None)
        self.assertEqual(result['hospital'], self.h1.id)
        self.assertEqual(result['user'], self.u1.id)

        # set wrong attribute
        response = client.patch('/en/api/client/{}/'.format(str(client1.client_id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'status': 'will fail'
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 400)

        # set wrong id
        response = client.patch('/en/api/client/100/',
                                data=json.dumps({
                                    'status': status
                                }),
                                follow=True)
        self.assertEqual(response.status_code, 404)

        # create client
        response = client.post('/en/api/client/',
                               content_type='application/json',
                               data=json.dumps({
                                   'client_id': 'client_id_2',
                                   'status': ClientStatus.O.name,
                                   'ambulance': None,
                                   'hospital': self.h2.id
                               }),
                               follow=True)
        self.assertEqual(response.status_code, 201)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ClientSerializer(Client.objects.get(client_id='client_id_2')).data
        self.assertDictEqual(result, answer)

        # retrieve client
        response = client.get('/en/api/client/{}/'.format('client_id_2'),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], ClientStatus.O.name)
        self.assertEqual(result['ambulance'], None)
        self.assertEqual(result['hospital'], self.h2.id)
        self.assertEqual(result['user'], self.u1.id)

        # create client as update
        response = client.post('/en/api/client/',
                               content_type='application/json',
                               data=json.dumps({
                                   'client_id': 'client_id_2',
                                   'status': ClientStatus.O.name,
                                   'ambulance': self.a1.id
                               }),
                               follow=True)
        self.assertEqual(response.status_code, 201)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ClientSerializer(Client.objects.get(client_id='client_id_2')).data
        self.assertDictEqual(result, answer)

        # retrieve client
        response = client.get('/en/api/client/{}/'.format('client_id_2'),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['status'], ClientStatus.O.name)
        self.assertEqual(result['ambulance'], self.a1.id)
        self.assertEqual(result['hospital'], self.h2.id)
        self.assertEqual(result['user'], self.u1.id)

        # logout
        client.logout()

        #
        # # login as testuser2
        # client.login(username='testuser2', password='very_secret')
        #
        # # retrieve ambulance
        # response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
        #                       follow=True)
        # self.assertEqual(response.status_code, 200)
        # result = JSONParser().parse(BytesIO(response.content))
        # answer = AmbulanceSerializer(self.a3).data
        # self.assertDictEqual(result, answer)
        #
        # # set status ambulance
        # status = AmbulanceStatus.OS.name
        # response = client.patch('/en/api/ambulance/{}/'.format(str(self.a3.id)),
        #                         content_type='application/json',
        #                         data=json.dumps({
        #                             'status': status,
        #                         }),
        #                         follow=True)
        # self.assertEqual(response.status_code, 200)
        # result = JSONParser().parse(BytesIO(response.content))
        # answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a3.id)).data
        # self.assertDictEqual(result, answer)
        #
        # # retrieve new ambulance status
        # response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
        #                       follow=True)
        # self.assertEqual(response.status_code, 200)
        # result = JSONParser().parse(BytesIO(response.content))
        # self.assertEqual(result['status'], status)
        #
        # # set location
        # timestamp = timezone.now()
        # location = {'latitude': -2., 'longitude': 7.}
        #
        # response = client.patch('/en/api/ambulance/{}/'.format(str(self.a3.id)),
        #                         content_type='application/json',
        #                         data=json.dumps({
        #                             'location': point2str(location),
        #                             'timestamp': date2iso(timestamp),
        #                         }),
        #                         follow=True)
        # self.assertEqual(response.status_code, 200)
        # result = JSONParser().parse(BytesIO(response.content))
        # answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a3.id)).data
        # if math.fabs(answer['orientation'] - result['orientation']) < 1e-4:
        #     answer['orientation'] = result['orientation']
        # self.assertDictEqual(result, answer)
        #
        # # retrieve new ambulance location
        # response = client.get('/en/api/ambulance/{}/'.format(str(self.a3.id)),
        #                       follow=True)
        # self.assertEqual(response.status_code, 200)
        # result = JSONParser().parse(BytesIO(response.content))
        # self.assertEqual(result['status'], status)
        # self.assertEqual(result['location'], point2str(location))
        # self.assertEqual(result['timestamp'], date2iso(timestamp))
        #
        # # set status ambulance
        # status = AmbulanceStatus.OS.name
        # response = client.patch('/en/api/ambulance/{}/'.format(str(self.a1.id)),
        #                         content_type='application/json',
        #                         data=json.dumps({
        #                             'status': status,
        #                         }),
        #                         follow=True)
        # self.assertEqual(response.status_code, 404)
        #
        # # set status ambulance
        # status = AmbulanceStatus.OS.name
        # response = client.patch('/en/api/ambulance/{}/'.format(str(self.a2.id)),
        #                         content_type='application/json',
        #                         data=json.dumps({
        #                             'status': status,
        #                         }),
        #                         follow=True)
        # self.assertEqual(response.status_code, 404)
        #
        # # logout
        # client.logout()
        #
        # # login as testuser1
        # client.login(username='testuser1', password='top_secret')
        #
        # # set status ambulance
        # status = AmbulanceStatus.OS.name
        # response = client.patch('/en/api/ambulance/{}/'.format(str(self.a1.id)),
        #                         content_type='application/json',
        #                         data=json.dumps({
        #                             'status': status,
        #                         }),
        #                         follow=True)
        # self.assertEqual(response.status_code, 404)
        #
        # # set status ambulance
        # status = AmbulanceStatus.OS.name
        # response = client.patch('/en/api/ambulance/{}/'.format(str(self.a2.id)),
        #                         content_type='application/json',
        #                         data=json.dumps({
        #                             'status': status,
        #                         }),
        #                         follow=True)
        # self.assertEqual(response.status_code, 404)
        #
        # # set status ambulance
        # status = AmbulanceStatus.OS.name
        # response = client.patch('/en/api/ambulance/{}/'.format(str(self.a3.id)),
        #                         content_type='application/json',
        #                         data=json.dumps({
        #                             'status': status,
        #                         }),
        #                         follow=True)
        # self.assertEqual(response.status_code, 404)
        #
        # # logout
        # client.logout()

