import logging

from django.test import Client
from django.conf import settings

from emstrack.tests.util import date2iso

from login.tests.setup_data import TestSetup

from ambulance.models import CallStatus, CallPriority, LocationType, WaypointStatus, Call, Patient, AmbulanceCall
from ambulance.serializers import CallSerializer, PatientSerializer, AmbulanceCallSerializer

logger = logging.getLogger(__name__)


class TestCallAPI(TestSetup):

    def test_call_create_viewset(self):

        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [
                {
                    'ambulance_id': self.a1.id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'some street'
                            }
                        },
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'type': LocationType.w.name,
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                }
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': self.a2.id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '321',
                                'street': 'another street'
                            }
                        }
                    ]
                }
            ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        c1 = Call.objects.get(status=CallStatus.P.name)
        serializer = CallSerializer(c1)

        expected_patient_set = PatientSerializer(Patient.objects.filter(call_id=c1.id), many=True).data
        expected_ambulancecall_set = AmbulanceCallSerializer(AmbulanceCall.objects.filter(call_id=c1.id), many=True).data

        self.assertEqual(len(expected_patient_set), 2)
        self.assertEqual(len(expected_ambulancecall_set[0]['waypoint_set'])
                         + len(expected_ambulancecall_set[1]['waypoint_set']), 3)

        expected = {
            'id': c1.id,
            'status': c1.status,
            'details': c1.details,
            'priority': c1.priority,
            'priority_code': c1.priority_code,
            'radio_code': c1.radio_code,
            'created_at': date2iso(c1.created_at),
            'pending_at': date2iso(c1.pending_at),
            'started_at': date2iso(c1.started_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'sms_notifications': [],
            'ambulancecall_set': expected_ambulancecall_set,
            'patient_set': expected_patient_set,
            'callnote_set': []
        }

        result = serializer.data
        self.assertCountEqual(result['ambulancecall_set'],
                              expected['ambulancecall_set'])
        self.assertCountEqual(result['patient_set'],
                              expected['patient_set'])
        expected['ambulancecall_set'] = []
        result['ambulancecall_set'] = []
        expected['patient_set'] = []
        result['patient_set'] = []
        self.assertDictEqual(result, expected)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser3', password='highly_secret')

        # Will fail for anyone not superuser or staff or dispatcher
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a2.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()

        # login as staff
        client.login(username='staff', password='so_secret')

        # Should not fail, is staff
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a2.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 201)

        # logout
        client.logout()

        # login as dispatcher
        client.login(username='testuser2', password='very_secret')

        # Should not fail, is dispatcher
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a3.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 201)

        # Should fail, dispatcher but not in authorized list of ambulances
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a1.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 403)

        # Should fail, dispatcher but not in authorized list of ambulances
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a3.id}, {'ambulance_id': self.a1.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()

    def test_call_viewset_update(self):

        # Pending Call with Ambulancecall_Set will create ambulancecalls
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [
                {
                    'ambulance_id': self.a1.id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'some street'
                            }
                        },
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'type': LocationType.w.name,
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                }
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': self.a2.id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '321',
                                'street': 'another street'
                            }
                        }
                    ]
                }
            ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)
        self.assertNotEqual(call.pending_at, None)
        self.assertEqual(call.started_at, None)
        self.assertEqual(call.ended_at, None)

        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # post call data
        data = {
            'status': CallStatus.S.name,
            'priority': CallPriority.D.name
        }
        response = client.post('/en/api/call/{}/'.format(call.id), data, content_type='application/json')
        self.assertEqual(response.status_code, 405)

        # partial update call data
        response = client.patch('/en/api/call/{}/'.format(call.id), data, content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 200)

        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)
        self.assertEqual(call.priority, CallPriority.D.name)
        self.assertNotEqual(call.pending_at, None)
        self.assertNotEqual(call.started_at, None)
        self.assertEqual(call.ended_at, None)
        started_at = call.started_at

        # partial update patient set
        patient_set = PatientSerializer(call.patient_set.all(), many=True).data
        patient_set[0]['age'] = 5
        patient_set[1]['age'] = 12
        logger.debug(patient_set)

        data = {
            'patient_set': patient_set
        }
        response = client.patch('/en/api/call/{}/'.format(call.id), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)
        self.assertEqual(call.priority, CallPriority.D.name)
        self.assertCountEqual(patient_set, PatientSerializer(call.patient_set.all(), many=True).data)
        self.assertEqual(call.started_at, started_at)

        # partial update patient set with addition
        patient_set = PatientSerializer(call.patient_set.all(), many=True).data
        patient_set.append({'name': 'someone', 'age': 14})
        logger.debug(patient_set)

        data = {
            'patient_set': patient_set
        }
        response = client.patch('/en/api/call/{}/'.format(call.id), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)
        self.assertEqual(call.priority, CallPriority.D.name)
        self.assertEqual(len(patient_set), len(PatientSerializer(call.patient_set.all(), many=True).data))
        self.assertEqual(call.started_at, started_at)

        # partial update patient set with addition and removal
        patient_set = PatientSerializer(call.patient_set.all(), many=True).data
        del patient_set[0]
        patient_set.append({'name': 'someone else', 'age': 17})

        data = {
            'patient_set': patient_set
        }
        response = client.patch('/en/api/call/{}/'.format(call.id), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)
        self.assertEqual(call.priority, CallPriority.D.name)
        self.assertEqual(len(patient_set), len(PatientSerializer(call.patient_set.all(), many=True).data))
        self.assertEqual(call.started_at, started_at)

        # partial update patient set with addition with null age
        patient_set = PatientSerializer(call.patient_set.all(), many=True).data
        patient_set.append({'name': 'someone else else'})

        data = {
            'patient_set': patient_set
        }
        response = client.patch('/en/api/call/{}/'.format(call.id), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)
        self.assertEqual(call.priority, CallPriority.D.name)
        self.assertEqual(len(patient_set), len(PatientSerializer(call.patient_set.all(), many=True).data))
        self.assertEqual(call.started_at, started_at)

        # partial update patient remove all patients
        patient_set = []

        data = {
            'patient_set': patient_set
        }
        response = client.patch('/en/api/call/{}/'.format(call.id), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)
        self.assertEqual(call.priority, CallPriority.D.name)
        self.assertEqual(len(patient_set), len(PatientSerializer(call.patient_set.all(), many=True).data))
        self.assertEqual(call.started_at, started_at)

        # logout
        client.logout()

    def test_call_abort_viewset(self):

        # instantiate client
        client = Client()

        # login as staff
        client.login(username='staff', password='so_secret')

        # Should not fail, is staff
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a2.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        call = JSONParser().parse(BytesIO(response.content))

        # abort
        response = client.get('/en/api/call/{}/abort/'.format(call['id']))
        self.assertEqual(response.status_code, 200)

        # Should not fail, is staff
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a2.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        call = JSONParser().parse(BytesIO(response.content))

        # logout
        client.logout()

        # login as dispatcher
        client.login(username='testuser2', password='very_secret')

        # Should fail, dispatcher but not in authorized list of ambulances
        response = client.get('/en/api/call/{}/abort/'.format(call['id']))
        self.assertEqual(response.status_code, 404)

        # Should not fail, is dispatcher
        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'sms_notifications': [],
            'ambulancecall_set': [{'ambulance_id': self.a3.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        call = JSONParser().parse(BytesIO(response.content))

        # abort
        response = client.get('/en/api/call/{}/abort/'.format(call['id']))
        self.assertEqual(response.status_code, 200)

        # logout
        client.logout()

    def test_call_list_viewset(self):

        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        response = client.get('/en/api/call/', follow=True)
        self.assertEquals(response.status_code, 200)

        result = JSONParser().parse(BytesIO(response.content))
        answer = CallSerializer(Call.objects.all(), many=True).data
        self.assertCountEqual(result, answer)

        # test_call_list_viewset_one_entry

        c1 = Call.objects.create(details='nani', updated_by=self.u1)

        response = client.get('/en/api/call/', follow=True)
        self.assertEquals(response.status_code, 200)

        result = JSONParser().parse(BytesIO(response.content))
        answer = CallSerializer(Call.objects.all(), many=True).data
        self.assertCountEqual(result, answer)

        # test_call_list_viewset_two_entries:

        c2 = Call.objects.create(details='suhmuh', updated_by=self.u1)

        response = client.get('/en/api/call/', follow=True)
        self.assertEquals(response.status_code, 200)

        result = JSONParser().parse(BytesIO(response.content))
        answer = CallSerializer(Call.objects.all(), many=True).data
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        response = client.get('/en/api/call/', follow=True)
        self.assertEquals(response.status_code, 200)

        result = JSONParser().parse(BytesIO(response.content))
        answer = CallSerializer([], many=True).data
        self.maxDiff = None
        self.assertCountEqual(result, answer)

        # add ambulances to calls, can only read a3
        AmbulanceCall.objects.create(call=c1, ambulance=self.a3, updated_by=self.u1)
        AmbulanceCall.objects.create(call=c2, ambulance=self.a2, updated_by=self.u1)

        response = client.get('/en/api/call/', follow=True)
        self.assertEquals(response.status_code, 200)

        result = JSONParser().parse(BytesIO(response.content))
        answer = CallSerializer([c1], many=True).data
        self.assertCountEqual(result, answer)

        # add second ambulance to call
        AmbulanceCall.objects.create(call=c1, ambulance=self.a1, updated_by=self.u1)

        response = client.get('/en/api/call/', follow=True)
        self.assertEquals(response.status_code, 200)

        result = JSONParser().parse(BytesIO(response.content))
        answer = CallSerializer([c1], many=True).data
        logger.debug(result)
        logger.debug(answer)
        self.assertEqual(len(result), 1)
        self.assertCountEqual(result, answer)

        # logout
        client.logout()

    def test_call_list_view(self):

        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        response = client.get(reverse('ambulance:call_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambulance/call_list.html')

        # test_call_list_view_one_entry

        c1 = Call.objects.create(details='nani', updated_by=self.u1)

        response = client.get(reverse('ambulance:call_list'))
        self.assertContains(response, 'nani')

        # test_call_list_view_two_entries:

        c2 = Call.objects.create(details='suhmuh', updated_by=self.u1)

        response = client.get(reverse('ambulance:call_list'))
        self.assertContains(response, 'nani')
        self.assertContains(response, 'suhmuh')

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        response = client.get(reverse('ambulance:call_list'))
        self.assertEquals(response.status_code, 200)
        self.assertNotContains(response, 'nani')
        self.assertNotContains(response, 'suhmuh')

        # add ambulances to calls, can only read a3
        AmbulanceCall.objects.create(call=c1, ambulance=self.a3, updated_by=self.u1)
        AmbulanceCall.objects.create(call=c2, ambulance=self.a2, updated_by=self.u1)

        response = client.get(reverse('ambulance:call_list'))
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'nani')
        self.assertNotContains(response, 'suhmuh')

        # add second ambulance to call
        AmbulanceCall.objects.create(call=c1, ambulance=self.a1, updated_by=self.u1)

        response = client.get(reverse('ambulance:call_list'))
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'nani')
        self.assertNotContains(response, 'suhmuh')

        # logout
        client.logout()

    def test_call_detail_view(self):

        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        c1 = Call.objects.create(details="Test1", updated_by=self.u1)

        response = client.get(reverse('ambulance:call_detail', kwargs={'pk': c1.id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambulance/call_detail.html')

        # test_call_detail_view_entry
        c2 = Call.objects.create(details='suhmuh', updated_by=self.u1)

        response = client.get(reverse('ambulance:call_detail', kwargs={'pk': c2.id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambulance/call_detail.html')
        self.assertContains(response, 'suhmuh')

        # logout
        client.logout()

        # Tests for unprivileged user

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # add ambulances to calls, can only read a3, only one per call
        AmbulanceCall.objects.create(call=c1, ambulance=self.a3, updated_by=self.u1)
        AmbulanceCall.objects.create(call=c2, ambulance=self.a2, updated_by=self.u1)

        response = client.get(reverse('ambulance:call_detail', kwargs={'pk': c1.id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambulance/call_detail.html')
        self.assertContains(response, 'Test1')

        response = client.get(reverse('ambulance:call_detail', kwargs={'pk': c2.id}))
        self.assertEquals(response.status_code, 404)

        # add second ambulance to call
        AmbulanceCall.objects.create(call=c1, ambulance=self.a1, updated_by=self.u1)

        response = client.get(reverse('ambulance:call_detail', kwargs={'pk': c1.id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambulance/call_detail.html')
        self.assertContains(response, 'Test1')

        # logout
        client.logout()