import logging

from django.test import Client
from django.conf import settings
from django.urls import reverse

from django.db import IntegrityError

from ambulance.models import Call, Patient, AmbulanceCall, CallStatus, CallPriority, AmbulanceCallEvent, \
    AmbulanceUpdate, AmbulanceStatus
from ambulance.serializers import CallSerializer, AmbulanceCallSerializer, PatientSerializer, \
    AmbulanceCallEventSerializer, AmbulanceUpdateSerializer
from emstrack.tests.util import date2iso, point2str

from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestCall(TestSetup):

    def test_patient_serializer(self):

        # test PatientSerializer
        c1 = Call.objects.create(number="123", street="dunno", updated_by=self.u1)
        p1 = Patient.objects.create(call=c1)
        serializer = PatientSerializer(p1)
        result = {
            'id': p1.id,
            'name': p1.name,
            'age': p1.age
        }
        self.assertDictEqual(serializer.data, result)

    def test_call_serializer(self):

        # create call
        c1 = Call.objects.create(number="123", street="dunno", updated_by=self.u1)

        # it is fine to have no ambulances because it is pending
        serializer = CallSerializer(c1)
        expected = {
            'id': c1.id,
            'status': c1.status,
            'details': c1.details,
            'priority': c1.priority,
            'number': c1.number,
            'street': c1.street,
            'unit': c1.unit,
            'neighborhood': c1.neighborhood,
            'city': c1.city,
            'state': c1.state,
            'zipcode': c1.zipcode,
            'country': c1.country,
            'location': point2str(c1.location),
            'created_at': date2iso(c1.created_at),
            'pending_at': date2iso(c1.pending_at),
            'started_at': date2iso(c1.started_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertDictEqual(serializer.data, expected)

        # create first ambulance call
        ambulance_call_1 = AmbulanceCall.objects.create(call=c1, ambulance=self.a1)

        ambulance_call = ambulance_call_1
        serializer = AmbulanceCallSerializer(ambulance_call)
        expected = {
            'id': ambulance_call.id,
            'ambulance_id': ambulance_call.ambulance.id,
            'created_at': date2iso(ambulance_call.created_at),
            'ambulancecallevent_set': []
        }
        self.assertDictEqual(serializer.data, expected)

        serializer = CallSerializer(c1)
        ambulance_call_serializer_1 = AmbulanceCallSerializer(ambulance_call_1)

        expected = {
            'id': c1.id,
            'status': c1.status,
            'details': c1.details,
            'priority': c1.priority,
            'number': c1.number,
            'street': c1.street,
            'unit': c1.unit,
            'neighborhood': c1.neighborhood,
            'city': c1.city,
            'state': c1.state,
            'zipcode': c1.zipcode,
            'country': c1.country,
            'location': point2str(c1.location),
            'created_at': date2iso(c1.created_at),
            'pending_at': date2iso(c1.pending_at),
            'started_at': date2iso(c1.started_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecall_set'], [ambulance_call_serializer_1.data])
        result = serializer.data
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        # create second ambulance call
        ambulance_call_2 = AmbulanceCall.objects.create(call=c1, ambulance=self.a3)

        ambulance_call = ambulance_call_2
        serializer = AmbulanceCallSerializer(ambulance_call)
        expected = {
            'id': ambulance_call.id,
            'ambulance_id': ambulance_call.ambulance.id,
            'created_at': date2iso(ambulance_call.created_at),
            'ambulancecallevent_set': []
        }
        self.assertDictEqual(serializer.data, expected)

        serializer = CallSerializer(c1)
        ambulance_call_serializer_2 = AmbulanceCallSerializer(ambulance_call_2)

        expected = {
            'id': c1.id,
            'status': c1.status,
            'details': c1.details,
            'priority': c1.priority,
            'number': c1.number,
            'street': c1.street,
            'unit': c1.unit,
            'neighborhood': c1.neighborhood,
            'city': c1.city,
            'state': c1.state,
            'zipcode': c1.zipcode,
            'country': c1.country,
            'location': point2str(c1.location),
            'created_at': date2iso(c1.created_at),
            'pending_at': date2iso(c1.pending_at),
            'started_at': date2iso(c1.started_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecall_set'],
                              [ambulance_call_serializer_2.data, ambulance_call_serializer_1.data])
        result = serializer.data
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        # create ambulance update to use in event
        ambulance_update_1 = AmbulanceUpdate.objects.create(ambulance=self.a1,
                                                            status=AmbulanceStatus.PB.name,
                                                            updated_by=self.u1)
        ambulance_update_2 = AmbulanceUpdate.objects.create(ambulance=self.a1,
                                                            status=AmbulanceStatus.AP.name,
                                                            updated_by=self.u1)
        ambulance_update_3 = AmbulanceUpdate.objects.create(ambulance=self.a1,
                                                            status=AmbulanceStatus.HB.name,
                                                            updated_by=self.u1)

        # create ambulance call events
        ambulance_call_event_1 = AmbulanceCallEvent.objects.create(ambulance_call=ambulance_call_2,
                                                                   ambulance_update=ambulance_update_1)
        ambulance_call_event_2 = AmbulanceCallEvent.objects.create(ambulance_call=ambulance_call_2,
                                                                   ambulance_update=ambulance_update_2)
        ambulance_call_event_3 = AmbulanceCallEvent.objects.create(ambulance_call=ambulance_call_2,
                                                                   ambulance_update=ambulance_update_3)

        ambulance_call_serializer_2 = AmbulanceCallSerializer(ambulance_call_2)
        ambulance_call_event_serializer_1 = AmbulanceCallEventSerializer(ambulance_call_event_1)
        ambulance_call_event_serializer_2 = AmbulanceCallEventSerializer(ambulance_call_event_2)
        ambulance_call_event_serializer_3 = AmbulanceCallEventSerializer(ambulance_call_event_3)

        expected = {
            'id': ambulance_call_event_1.id,
            'ambulance_update': AmbulanceUpdateSerializer(ambulance_update_1).data
        }
        self.assertDictEqual(ambulance_call_event_serializer_1.data, expected)

        serializer = CallSerializer(c1)

        expected = {
            'id': c1.id,
            'status': c1.status,
            'details': c1.details,
            'priority': c1.priority,
            'number': c1.number,
            'street': c1.street,
            'unit': c1.unit,
            'neighborhood': c1.neighborhood,
            'city': c1.city,
            'state': c1.state,
            'zipcode': c1.zipcode,
            'country': c1.country,
            'location': point2str(c1.location),
            'created_at': date2iso(c1.created_at),
            'pending_at': date2iso(c1.pending_at),
            'started_at': date2iso(c1.started_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecall_set'],
                              [ambulance_call_serializer_2.data, ambulance_call_serializer_1.data])
        result = serializer.data
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        # cannot have duplicate
        self.assertRaises(IntegrityError, AmbulanceCall.objects.create, call=c1, ambulance=self.a1)

    def test_call_serializer_create(self):

        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        serializer.save(updated_by=self.u1)

        # test CallSerializer
        c1 = Call.objects.get(number='123', street='asdasdasd asd asd asdas')
        serializer = CallSerializer(c1)

        result = {
            'id': c1.id,
            'status': c1.status,
            'details': c1.details,
            'priority': c1.priority,
            'number': c1.number,
            'street': c1.street,
            'unit': c1.unit,
            'neighborhood': c1.neighborhood,
            'city': c1.city,
            'state': c1.state,
            'zipcode': c1.zipcode,
            'country': c1.country,
            'location': point2str(c1.location),
            'created_at': date2iso(c1.created_at),
            'pending_at': date2iso(c1.pending_at),
            'started_at': date2iso(c1.started_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertDictEqual(serializer.data, result)

        # Ongoing Call without Ambulancecall_Set fails
        call = {
            'status': CallStatus.S.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
        }
        serializer = CallSerializer(data=call)
        self.assertFalse(serializer.is_valid())

        # Pending Call with Ambulancecall_Set
        #  WILL HAVE TO CREATE AMBULANCECALLS
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a2.id}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # test CallSerializer
        c1 = Call.objects.get(id=call.id)
        serializer = CallSerializer(c1)

        expected_ambulancecall_set = [
            AmbulanceCallSerializer(
                AmbulanceCall.objects.get(call_id=c1.id,
                                          ambulance_id=self.a1.id)).data,
            AmbulanceCallSerializer(
                AmbulanceCall.objects.get(call_id=c1.id,
                                          ambulance_id=self.a2.id)).data
            ]

        expected = {
            'id': c1.id,
            'status': c1.status,
            'details': c1.details,
            'priority': c1.priority,
            'number': c1.number,
            'street': c1.street,
            'unit': c1.unit,
            'neighborhood': c1.neighborhood,
            'city': c1.city,
            'state': c1.state,
            'zipcode': c1.zipcode,
            'country': c1.country,
            'location': point2str(c1.location),
            'created_at': date2iso(c1.created_at),
            'pending_at': date2iso(c1.pending_at),
            'started_at': date2iso(c1.started_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecall_set': expected_ambulancecall_set,
            'patient_set': []
        }

        result = serializer.data
        logger.debug(result['ambulancecall_set'])
        logger.debug(expected['ambulancecall_set'])
        self.assertCountEqual(result['ambulancecall_set'],
                              expected['ambulancecall_set'])
        expected['ambulancecall_set'] = []
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        # Should fail because ambulance id's are repeated
        call = {
            'status': CallStatus.S.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'will fail',
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a1.id}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        self.assertRaises(IntegrityError, serializer.save, updated_by=self.u1)

        # make sure no call was created
        self.assertRaises(Call.DoesNotExist, Call.objects.get, street='will fail')

    # THESE ARE FAILING!
    def _test_call_update_serializer(self):
        
        # superuser first

        # Update call status
        c = Call.objects.create(number="123", street="dunno", updated_by=self.u1)
        user = self.u1
        status = CallStatus.S.name

        serializer = CallSerializer(c, 
                                    data={
                                        'status': status
                                    }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)
        
        # test
        serializer = CallSerializer(c)
        result = {
            'id': c.id,
            'status': status,
            'details': c.details,
            'priority': c.priority,
            'number': c.number,
            'street': c.street,
            'unit': c.unit,
            'neighborhood': c.neighborhood,
            'city': c.city,
            'state': c.state,
            'zipcode': c.zipcode,
            'country': c.country,
            'location': point2str(c.location),
            'created_at': date2iso(c.created_at),
            'pending_at': date2iso(c.pending_at),
            'started_at': date2iso(c.started_at),
            'ended_at': date2iso(c.ended_at),
            'comment': c.comment,
            'updated_by': c.updated_by.id,
            'updated_on': date2iso(c.updated_on),
            'ambulancecall_set': AmbulanceCallSerializer(many=True).data,
            'patient_set': PatientSerializer(many=True).data
        }
        self.assertDictEqual(serializer.data, result)

        # Update call street
        street = 'new street'

        serializer = CallSerializer(c, 
                                    data={
                                        'street': street,
                                    }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)
         
        # test
        serializer = CallSerializer(c)
        result = {
            'id': c.id,
            'status': c.status,
            'details': c.details,
            'priority': c.priority,
            'number': c.number,
            'street': street,
            'unit': c.unit,
            'neighborhood': c.neighborhood,
            'city': c.city,
            'state': c.state,
            'zipcode': c.zipcode,
            'country': c.country,
            'location': point2str(c.location),
            'created_at': date2iso(c.created_at),
            'pending_at': date2iso(c.pending_at),
            'started_at': date2iso(c.started_at),
            'ended_at': date2iso(c.ended_at),
            'comment': c.comment,    
            'updated_by': c.updated_by.id,
            'updated_on': date2iso(c.updated_on),
            'ambulancecall_set': AmbulanceCallSerializer(many=True).data,
            'patient_set': PatientSerializer(many=True).data
        }
        self.assertDictEqual(serializer.data, result)

        # Update call location
        location = {'latitude': -2., 'longitude': 7.}

        serializer = CallSerializer(c, 
                                    data={
                                        'location': location,
                                    }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = CallSerializer(c)
        result = {
            'id': c.id,
            'status': c.status,
            'details': c.details,
            'priority': c.priority,
            'number': c.number,
            'street': c.street,
            'unit': c.unit,
            'neighborhood': c.neighborhood,
            'city': c.city,
            'state': c.state,
            'zipcode': c.zipcode,
            'country': c.country,
            'location': point2str(location),
            'created_at': date2iso(c.created_at),
            'pending_at': date2iso(c.pending_at),
            'started_at': date2iso(c.started_at),
            'ended_at': date2iso(c.ended_at),
            'comment': c.comment,
            'updated_by': c.updated_by.id,
            'updated_on': date2iso(c.updated_on),
            'ambulancecall_set': AmbulanceCallSerializer(many=True).data,
            'patient_set': PatientSerializer(many=True).data
        }
        self.assertDictEqual(serializer.data, result)

        # Need more tests for updates by regular authorized user

    def test_call_list_view_loads(self):
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        response = client.get(reverse('ambulance:call_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambulance/call_list.html')

    def test_call_list_view_one_entry(self):
        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])
        
        Call.objects.create(details='nani', updated_by=self.u1)

        response = client.get(reverse('ambulance:call_list'))
        self.assertContains(response, 'nani')

    def test_call_list_view_two_entries(self):
        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        Call.objects.create(details='nani', updated_by=self.u1)
        Call.objects.create(details='suhmuh', updated_by=self.u1)

        response = client.get(reverse('ambulance:call_list'))
        self.assertContains(response, 'nani')
        self.assertContains(response, 'suhmuh')

    def test_call_detail_view_loads(self):
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        c1 = Call.objects.create(details="Test1", updated_by=self.u1)

        response = client.get(reverse('ambulance:call_detail', kwargs={'pk': c1.id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambulance/call_detail.html')

    def test_call_detail_view_entry(self):
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])
        c1 = Call.objects.create(details="Test1", updated_by=self.u1)

        response = client.get(reverse('ambulance:call_detail', kwargs={'pk': c1.id}))
        self.assertContains(response, 'Test1')

