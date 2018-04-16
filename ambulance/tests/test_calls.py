import logging

from django.db import IntegrityError
from rest_framework.parsers import JSONParser

from ambulance.models import Call, Patient, AmbulanceCallTime, CallStatus, CallPriority
from ambulance.serializers import CallSerializer, AmbulanceCallTimeSerializer, PatientSerializer
from emstrack.tests.util import date2iso, point2str

from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)

class TestCall(TestSetup):

    def test_call_serializer(self):

        c1 = Call.objects.create(number="123", street="dunno", updated_by=self.u1)

        ambCallTime1 = AmbulanceCallTime.objects.create(call=c1, ambulance=self.a1)

        ambCallTime = ambCallTime1
        serializer = AmbulanceCallTimeSerializer(ambCallTime)
        result = {
            'id': ambCallTime.id,
            'call_id': ambCallTime.call.id,
            'ambulance_id': ambCallTime.ambulance.id,
            'dispatch_time': date2iso(ambCallTime.dispatch_time),
            'departure_time': date2iso(ambCallTime.departure_time),
            'patient_time': date2iso(ambCallTime.patient_time),
            'hospital_time': date2iso(ambCallTime.hospital_time),
            'end_time': date2iso(ambCallTime.end_time)
        }
        self.assertDictEqual(serializer.data, result)

        ambCallTime2 = AmbulanceCallTime.objects.create(call=c1, ambulance=self.a3)

        ambCallTime = ambCallTime2
        serializer = AmbulanceCallTimeSerializer(ambCallTime)
        result = {
            'id': ambCallTime.id,
            'call_id': ambCallTime.call.id,
            'ambulance_id': ambCallTime.ambulance.id,
            'dispatch_time': date2iso(ambCallTime.dispatch_time),
            'departure_time': date2iso(ambCallTime.departure_time),
            'patient_time': date2iso(ambCallTime.patient_time),
            'hospital_time': date2iso(ambCallTime.hospital_time),
            'end_time': date2iso(ambCallTime.end_time)
        }
        self.assertDictEqual(serializer.data, result)

        serializer = CallSerializer(c1)
        ambCallTimeSerializer1 = AmbulanceCallTimeSerializer(ambCallTime1)
        ambCallTimeSerializer2 = AmbulanceCallTimeSerializer(ambCallTime2)

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
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecalltime_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecalltime_set'],
                              [ambCallTimeSerializer2.data, ambCallTimeSerializer1.data])
        result = serializer.data
        result['ambulancecalltime_set'] = []
        self.assertDictEqual(result, expected)

        with self.assertRaises(IntegrityError) as context:
            AmbulanceCallTime.objects.create(call=c1, ambulance = self.a1)

    def test_call_serializer_create(self):

        call = {
            'status': CallStatus.O,
            'priority': CallPriority.B,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        logger.d('errors = {}'.format(serializer.errors))
        serializer.save(updated_by=self.u1)

        # test CallSerializer
        c1 = Call.objects.get(number='123',street='asdasdasd asd asd asdas')
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
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
            'ambulancecalltime_set': [],
            'patient_set': []
        }
        self.assertDictEqual(serializer.data, result)


    def test_call_update_serializer(self):
        
        # superuser first

        # Update call status
        c = Call.objects.create(number="123", street="dunno", updated_by=self.u1)
        user = self.u1
        status = CallStatus.O.name

        serializer = CallSerializer(c, 
                                    data={
                                        'status': status,
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
            'ended_at': date2iso(c.ended_at),
            'comment': c.comment,
            'updated_by': c.updated_by.id,
            'updated_on': date2iso(c.updated_on),
            'ambulancecalltime_set': AmbulanceCallTimeSerializer(many=True).data,
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
            'ended_at': date2iso(c.ended_at),
            'comment': c.comment,    
            'updated_by': c.updated_by.id,
            'updated_on': date2iso(c.updated_on),
            'ambulancecalltime_set': AmbulanceCallTimeSerializer(many=True).data,
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
            'ended_at': date2iso(c.ended_at),
            'comment': c.comment,
            'updated_by': c.updated_by.id,
            'updated_on': date2iso(c.updated_on),
            'ambulancecalltime_set': AmbulanceCallTimeSerializer(many=True).data,
            'patient_set': PatientSerializer(many=True).data
        }
        self.assertDictEqual(serializer.data, result)
	
        # Need more tests for updates by regular authorized user


    def test_patient_serializer(self):

        # test PatientSerializer
        c1 = Call.objects.create(number="123", street="dunno", updated_by=self.u1)
        p1 = Patient.objects.create(call=c1)
        serializer = PatientSerializer(p1)
        result = {
            'id': p1.id,
            'call_id': p1.call.id,
            'name': p1.name,
            'age': p1.age
        }
        self.assertDictEqual(serializer.data, result)

