import logging
import time

from django.test import Client
from django.conf import settings
from django.urls import reverse

from django.db import IntegrityError
from django.utils import timezone

from rest_framework.parsers import JSONParser
from rest_framework import serializers
from io import BytesIO
import json

from ambulance.models import Call, Patient, AmbulanceCall, CallStatus, CallPriority, \
    AmbulanceUpdate, AmbulanceStatus, Waypoint, Location, LocationType, WaypointStatus, AmbulanceCallStatus
from ambulance.serializers import CallSerializer, AmbulanceCallSerializer, PatientSerializer, \
    AmbulanceUpdateSerializer, WaypointSerializer, LocationSerializer
from emstrack.tests.util import date2iso, point2str

from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestCall(TestSetup):

    def test_patient_serializer(self):

        # test PatientSerializer
        c1 = Call.objects.create(updated_by=self.u1)

        # serialization
        p1 = Patient.objects.create(call=c1)
        serializer = PatientSerializer(p1)
        result = {
            'id': p1.id,
            'name': '',
            'age': None
        }
        self.assertDictEqual(serializer.data, result)

        # deserialization
        data = {
            'name': 'Jose',
            'age': 3
        }
        serializer = PatientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save(call_id=c1.id)

        p1 = Patient.objects.get(name='Jose')
        serializer = PatientSerializer(p1)
        result = {
            'id': p1.id,
            'name': 'Jose',
            'age': 3
        }
        self.assertDictEqual(serializer.data, result)

        # deserialization
        data = {
            'name': 'Maria',
        }
        serializer = PatientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save(call_id=c1.id)

        p1 = Patient.objects.get(name='Maria')
        serializer = PatientSerializer(p1)
        result = {
            'id': p1.id,
            'name': 'Maria',
            'age': None
        }
        self.assertDictEqual(serializer.data, result)

    def test_location_serializer(self):

        wpl_1 = Location.objects.create(type=LocationType.i.name, updated_by=self.u1)
        serializer = LocationSerializer(wpl_1)
        result = {
            'id': wpl_1.id,
            'type': LocationType.i.name,
            'location': point2str(wpl_1.location),
            'number': wpl_1.number,
            'street': wpl_1.street,
            'unit': wpl_1.unit,
            'neighborhood': wpl_1.neighborhood,
            'city': wpl_1.city,
            'state': wpl_1.state,
            'zipcode': wpl_1.zipcode,
            'country': wpl_1.country,
            'name': wpl_1.name,
            'comment': wpl_1.comment,
            'updated_by': wpl_1.updated_by.id,
            'updated_on': date2iso(wpl_1.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        wpl_2 = Location.objects.create(type=LocationType.h.name, number='123', street='adsasd', updated_by=self.u1)
        serializer = LocationSerializer(wpl_2)
        result = {
            'id': wpl_2.id,
            'type': LocationType.h.name,
            'location': point2str(wpl_2.location),
            'number': '123',
            'street': 'adsasd',
            'unit': wpl_2.unit,
            'neighborhood': wpl_2.neighborhood,
            'city': wpl_2.city,
            'state': wpl_2.state,
            'zipcode': wpl_2.zipcode,
            'country': wpl_2.country,
            'name': wpl_2.name,
            'comment': wpl_2.comment,
            'updated_by': wpl_2.updated_by.id,
            'updated_on': date2iso(wpl_2.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

    def test_waypoint_serializer(self):

        # create call
        c_1 = Call.objects.create(updated_by=self.u1)

        # create ambulance call
        ac_1 = AmbulanceCall.objects.create(call=c_1, ambulance=self.a1, updated_by=self.u1)

        # serialization
        wpl_1 = Location.objects.create(type=LocationType.i.name, updated_by=self.u1)
        wpl_1_serializer = LocationSerializer(wpl_1)
        wp_1 = Waypoint.objects.create(ambulance_call=ac_1, order=0, status=WaypointStatus.C.name,
                                       location=wpl_1, updated_by=self.u1)
        serializer = WaypointSerializer(wp_1)
        result = {
            'id': wp_1.id,
            'ambulance_call_id': ac_1.id,
            'order': 0,
            'status': WaypointStatus.C.name,
            'location': wpl_1_serializer.data,
            'comment': wp_1.comment,
            'updated_by': wp_1.updated_by.id,
            'updated_on': date2iso(wp_1.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        result = {
            'id': wpl_1.id,
            'type': LocationType.i.name,
            'location': point2str(wpl_1.location),
            'number': wpl_1.number,
            'street': wpl_1.street,
            'unit': wpl_1.unit,
            'neighborhood': wpl_1.neighborhood,
            'city': wpl_1.city,
            'state': wpl_1.state,
            'zipcode': wpl_1.zipcode,
            'country': wpl_1.country,
            'name': wpl_1.name,
            'comment': wpl_1.comment,
            'updated_by': wpl_1.updated_by.id,
            'updated_on': date2iso(wpl_1.updated_on)
        }
        self.assertDictEqual(serializer.data['location'], result)

        # serialization
        wpl_2 = Location.objects.create(type=LocationType.h.name, number='123', street='adsasd', updated_by=self.u1)
        wpl_2_serializer = LocationSerializer(wpl_2)
        wp_2 = Waypoint.objects.create(ambulance_call=ac_1, order=1, status=WaypointStatus.D.name,
                                       location=wpl_2, updated_by=self.u1)
        serializer = WaypointSerializer(wp_2)
        result = {
            'id': wp_2.id,
            'ambulance_call_id': ac_1.id,
            'order': 1,
            'status': WaypointStatus.D.name,
            'location': wpl_2_serializer.data,
            'comment': wp_2.comment,
            'updated_by': wp_2.updated_by.id,
            'updated_on': date2iso(wp_2.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        result = {
            'id': wpl_2.id,
            'type': LocationType.h.name,
            'location': point2str(wpl_2.location),
            'number': '123',
            'street': 'adsasd',
            'unit': wpl_2.unit,
            'neighborhood': wpl_2.neighborhood,
            'city': wpl_2.city,
            'state': wpl_2.state,
            'zipcode': wpl_2.zipcode,
            'country': wpl_2.country,
            'name': wpl_2.name,
            'comment': wpl_2.comment,
            'updated_by': wpl_2.updated_by.id,
            'updated_on': date2iso(wpl_2.updated_on)
        }
        self.assertDictEqual(serializer.data['location'], result)

    def test_waypoint_serializer_create(self):

        # create call
        c_1 = Call.objects.create(updated_by=self.u1)

        # create ambulance call
        ac_1 = AmbulanceCall.objects.create(call=c_1, ambulance=self.a1, updated_by=self.u1)

        # serialization
        data = {
            'order': 0,
            'status': WaypointStatus.C.name,
            'location': {
                'type': LocationType.i.name
            }
        }
        serializer = WaypointSerializer(data=data)
        serializer.is_valid()
        wp_1 = serializer.save(updated_by=self.u1, ambulance_call_id=ac_1.id)

        wpl_1 = wp_1.location
        wpl_1_serializer = LocationSerializer(wpl_1)
        serializer = WaypointSerializer(wp_1)
        result = {
            'id': wp_1.id,
            'ambulance_call_id': ac_1.id,
            'order': 0,
            'status': WaypointStatus.C.name,
            'location': wpl_1_serializer.data,
            'comment': wp_1.comment,
            'updated_by': wp_1.updated_by.id,
            'updated_on': date2iso(wp_1.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        result = {
            'id': wpl_1.id,
            'type': LocationType.i.name,
            'location': point2str(wpl_1.location),
            'number': wpl_1.number,
            'street': wpl_1.street,
            'unit': wpl_1.unit,
            'neighborhood': wpl_1.neighborhood,
            'city': wpl_1.city,
            'state': wpl_1.state,
            'zipcode': wpl_1.zipcode,
            'country': wpl_1.country,
            'name': wpl_1.name,
            'comment': wpl_1.comment,
            'updated_by': wpl_1.updated_by.id,
            'updated_on': date2iso(wpl_1.updated_on)
        }
        self.assertDictEqual(serializer.data['location'], result)

        # serialization
        data = {
            'order': 1,
            'status': WaypointStatus.V.name,
            'location': {
                'id': self.h1.id,
                'type': LocationType.h.name
            }
        }
        serializer = WaypointSerializer(data=data)
        serializer.is_valid()
        wp_2 = serializer.save(updated_by=self.u1,
                               ambulance_call_id=ac_1.id, publish=True)
    
        wpl_2 = self.h1.location_ptr
        wpl_2_serializer = LocationSerializer(wpl_2)
        logger.debug(wpl_2_serializer.data)
        serializer = WaypointSerializer(wp_2)
        logger.debug(serializer.data['location'])
        result = {
            'id': wp_2.id,
            'ambulance_call_id': ac_1.id,
            'order': 1,
            'status': WaypointStatus.V.name,
            'location': wpl_2_serializer.data,
            'comment': wp_2.comment,
            'updated_by': wp_2.updated_by.id,
            'updated_on': date2iso(wp_2.updated_on)
        }
        self.maxDiff = None
        self.assertDictEqual(serializer.data, result)
        result = {
            'id': wpl_2.id,
            'type': LocationType.h.name,
            'location': point2str(wpl_2.location),
            'number': wpl_2.number,
            'street': wpl_2.street,
            'unit': wpl_2.unit,
            'neighborhood': wpl_2.neighborhood,
            'city': wpl_2.city,
            'state': wpl_2.state,
            'zipcode': wpl_2.zipcode,
            'country': wpl_2.country,
            'name': wpl_2.name,
            'comment': wpl_2.comment,
            'updated_by': wpl_2.updated_by.id,
            'updated_on': date2iso(wpl_2.updated_on)
        }
        self.assertDictEqual(serializer.data['location'], result)

        # try to create hospital waypoint
        data = {
            'order': 1,
            'status': WaypointStatus.V.name,
            'location': {
                'type': LocationType.h.name
            }
        }
        serializer = WaypointSerializer(data=data)
        serializer.is_valid()
        self.assertRaises(serializers.ValidationError, serializer.save, updated_by=self.u1, ambulance_call_id=ac_1.id)

        # try to create waypoint without location
        data = {
            'order': 1,
            'status': WaypointStatus.V.name,
        }
        serializer = WaypointSerializer(data=data)
        serializer.is_valid()
        self.assertRaises(serializers.ValidationError, serializer.save, updated_by=self.u1, ambulance_call_id=ac_1.id)

    def test_waypoint_serializer_update(self):

        # create call
        c_1 = Call.objects.create(updated_by=self.u1)

        # create ambulance call
        ac_1 = AmbulanceCall.objects.create(call=c_1, ambulance=self.a1, updated_by=self.u1)

        # waypoint creation
        wpl_1 = Location.objects.create(type=LocationType.i.name, updated_by=self.u1)
        wp_1 = Waypoint.objects.create(ambulance_call=ac_1, order=0, status=WaypointStatus.C.name,
                                       location=wpl_1, updated_by=self.u1)

        wpl_2 = Location.objects.create(type=LocationType.w.name, number='123', street='adsasd', updated_by=self.u1)
        wp_2 = Waypoint.objects.create(ambulance_call=ac_1, order=1, status=WaypointStatus.D.name,
                                       location=wpl_2, updated_by=self.u1)

        wpl_3 = self.h1.location_ptr
        wp_3 = Waypoint.objects.create(ambulance_call=ac_1, order=1, status=WaypointStatus.V.name,
                                       location=wpl_3, updated_by=self.u1)

        wpl_1_serializer = LocationSerializer(wpl_1)
        serializer = WaypointSerializer(wp_1)
        result = {
            'id': wp_1.id,
            'ambulance_call_id': ac_1.id,
            'order': 0,
            'status': WaypointStatus.C.name,
            'location': wpl_1_serializer.data,
            'comment': wp_1.comment,
            'updated_by': wp_1.updated_by.id,
            'updated_on': date2iso(wp_1.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        result = {
            'id': wpl_1.id,
            'type': LocationType.i.name,
            'location': point2str(wpl_1.location),
            'number': wpl_1.number,
            'street': wpl_1.street,
            'unit': wpl_1.unit,
            'neighborhood': wpl_1.neighborhood,
            'city': wpl_1.city,
            'state': wpl_1.state,
            'zipcode': wpl_1.zipcode,
            'country': wpl_1.country,
            'name': wpl_1.name,
            'comment': wpl_1.comment,
            'updated_by': wpl_1.updated_by.id,
            'updated_on': date2iso(wpl_1.updated_on)
        }
        self.assertDictEqual(serializer.data['location'], result)

        # update waypoint 1
        data = {
            'order': 1,
            'status': WaypointStatus.V.name
        }
        serializer = WaypointSerializer(wp_1, data=data)
        serializer.is_valid()
        logger.debug(serializer.errors)
        wp_1 = serializer.save(updated_by=self.u1)

        wpl_1_serializer = LocationSerializer(wpl_1)
        serializer = WaypointSerializer(wp_1)
        result = {
            'id': wp_1.id,
            'ambulance_call_id': ac_1.id,
            'order': 1,
            'status': WaypointStatus.V.name,
            'location': wpl_1_serializer.data,
            'comment': wp_1.comment,
            'updated_by': wp_1.updated_by.id,
            'updated_on': date2iso(wp_1.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        result = {
            'id': wpl_1.id,
            'type': LocationType.i.name,
            'location': point2str(wpl_1.location),
            'number': wpl_1.number,
            'street': wpl_1.street,
            'unit': wpl_1.unit,
            'neighborhood': wpl_1.neighborhood,
            'city': wpl_1.city,
            'state': wpl_1.state,
            'zipcode': wpl_1.zipcode,
            'country': wpl_1.country,
            'name': wpl_1.name,
            'comment': wpl_1.comment,
            'updated_by': wpl_1.updated_by.id,
            'updated_on': date2iso(wpl_1.updated_on)
        }
        self.assertDictEqual(serializer.data['location'], result)

        # update waypoint 2
        data = {
            'order': 2,
            'status': WaypointStatus.C.name
        }
        serializer = WaypointSerializer(wp_2, data=data)
        serializer.is_valid()
        logger.debug(serializer.errors)
        wp_2 = serializer.save(updated_by=self.u1)

        wpl_2_serializer = LocationSerializer(wpl_2)
        serializer = WaypointSerializer(wp_2)
        result = {
            'id': wp_2.id,
            'ambulance_call_id': ac_1.id,
            'order': 2,
            'status': WaypointStatus.C.name,
            'location': wpl_2_serializer.data,
            'comment': wp_2.comment,
            'updated_by': wp_2.updated_by.id,
            'updated_on': date2iso(wp_2.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        result = {
            'id': wpl_2.id,
            'type': LocationType.w.name,
            'location': point2str(wpl_2.location),
            'number': wpl_2.number,
            'street': wpl_2.street,
            'unit': wpl_2.unit,
            'neighborhood': wpl_2.neighborhood,
            'city': wpl_2.city,
            'state': wpl_2.state,
            'zipcode': wpl_2.zipcode,
            'country': wpl_2.country,
            'name': wpl_2.name,
            'comment': wpl_2.comment,
            'updated_by': wpl_2.updated_by.id,
            'updated_on': date2iso(wpl_2.updated_on)
        }
        self.assertDictEqual(dict(serializer.data['location']), result)

        # update waypoint 3
        data = {
            'order': 2,
            'status': WaypointStatus.C.name,
            'location': {
                'id': 20,
                'type': LocationType.h.name
            }
        }
        serializer = WaypointSerializer(wp_3, data=data)
        serializer.is_valid()
        logger.debug(serializer.errors)
        self.assertRaises(serializers.ValidationError, serializer.save, updated_by=self.u1)

    def test_call_serializer(self):

        # create call
        c1 = Call.objects.create(updated_by=self.u1)

        # it is fine to have no ambulances because it is pending
        serializer = CallSerializer(c1)
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
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertDictEqual(serializer.data, expected)

        # create first ambulance call
        ambulance_call_1 = AmbulanceCall.objects.create(call=c1, ambulance=self.a1, updated_by=self.u1)

        ambulance_call = ambulance_call_1
        serializer = AmbulanceCallSerializer(ambulance_call)
        expected = {
            'id': ambulance_call.id,
            'ambulance_id': ambulance_call.ambulance.id,
            'comment': ambulance_call.comment,
            'updated_by': ambulance_call.updated_by.id,
            'updated_on': date2iso(ambulance_call.updated_on),
            'status': ambulance_call.status,
            'waypoint_set': []
        }
        self.assertDictEqual(serializer.data, expected)

        serializer = CallSerializer(c1)
        ambulance_call_serializer_1 = AmbulanceCallSerializer(ambulance_call_1)

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
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecall_set'], [ambulance_call_serializer_1.data])
        result = serializer.data
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        # set accepted
        ambulance_call_1.status = AmbulanceCallStatus.A.name
        ambulance_call_1.save()

        ambulance_call_serializer_1 = AmbulanceCallSerializer(ambulance_call_1)
        expected = {
            'id': ambulance_call.id,
            'ambulance_id': ambulance_call.ambulance.id,
            'comment': ambulance_call.comment,
            'updated_by': ambulance_call.updated_by.id,
            'updated_on': date2iso(ambulance_call.updated_on),
            'status': AmbulanceCallStatus.A.name,
            'waypoint_set': []
        }
        self.assertDictEqual(ambulance_call_serializer_1.data, expected)

        # create second ambulance call
        ambulance_call_2 = AmbulanceCall.objects.create(call=c1, ambulance=self.a3, updated_by=self.u1)

        ambulance_call = ambulance_call_2
        serializer = AmbulanceCallSerializer(ambulance_call)
        expected = {
            'id': ambulance_call.id,
            'ambulance_id': ambulance_call.ambulance.id,
            'comment': ambulance_call.comment,
            'updated_by': ambulance_call.updated_by.id,
            'updated_on': date2iso(ambulance_call.updated_on),
            'status': ambulance_call.status,
            'waypoint_set': []
        }
        self.assertDictEqual(serializer.data, expected)

        serializer = CallSerializer(c1)
        ambulance_call_serializer_2 = AmbulanceCallSerializer(ambulance_call_2)

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
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecall_set'],
                              [ambulance_call_serializer_2.data, ambulance_call_serializer_1.data])
        result = serializer.data
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        # set accepted
        ambulance_call_2.status = AmbulanceCallStatus.A.name
        ambulance_call_2.save()

        ambulance_call_serializer_2 = AmbulanceCallSerializer(ambulance_call_2)
        expected = {
            'id': ambulance_call.id,
            'ambulance_id': ambulance_call.ambulance.id,
            'comment': ambulance_call.comment,
            'updated_by': ambulance_call.updated_by.id,
            'updated_on': date2iso(ambulance_call.updated_on),
            'status': AmbulanceCallStatus.A.name,
            'waypoint_set': []
        }
        self.assertDictEqual(ambulance_call_serializer_2.data, expected)

        # Add waypoints to ambulancecalls
        wpl_1 = Location.objects.create(type=LocationType.i.name, updated_by=self.u1)
        wp_1 = Waypoint.objects.create(ambulance_call=ambulance_call_1, order=0, status=WaypointStatus.C.name,
                                       location=wpl_1, updated_by=self.u1)

        wpl_2 = Location.objects.create(type=LocationType.h.name, number='123', street='adsasd', updated_by=self.u2)
        wp_2 = Waypoint.objects.create(ambulance_call=ambulance_call_2, order=1, status=WaypointStatus.D.name,
                                       location=wpl_2, updated_by=self.u2)

        wp_3 = Waypoint.objects.create(ambulance_call=ambulance_call_2, order=2, status=WaypointStatus.V.name,
                                       location=self.h1, updated_by=self.u2)

        # create ambulance update to use in event
        self.a1.status = AmbulanceStatus.PB.name
        self.a1.timestamp = timezone.now()
        self.a1.save()
        ambulance_update_1 = AmbulanceUpdate.objects.get(status=AmbulanceStatus.PB.name)

        # set suspended
        ambulance_call_1.status = AmbulanceCallStatus.S.name
        ambulance_call_1.save()

        self.a1.status = AmbulanceStatus.AP.name
        self.a1.timestamp = timezone.now()
        self.a1.save()
        ambulance_update_2 = AmbulanceUpdate.objects.get(status=AmbulanceStatus.AP.name)

        # set accepted
        ambulance_call_1.status = AmbulanceCallStatus.A.name
        ambulance_call_1.save()

        self.a1status = AmbulanceStatus.HB.name
        self.a1.timestamp = timezone.now()
        self.a1.save()

        serializer = CallSerializer(c1)
        ambulance_call_serializer_1 = AmbulanceCallSerializer(ambulance_call_1)
        ambulance_call_serializer_2 = AmbulanceCallSerializer(ambulance_call_2)

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
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecall_set'],
                              [ambulance_call_serializer_2.data, ambulance_call_serializer_1.data])
        result = serializer.data
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        wp_1_serializer = WaypointSerializer(wp_1)
        result = {
            'id': wp_1.id,
            'ambulance_call_id': ambulance_call_1.id,
            'order': 0,
            'status': WaypointStatus.C.name,
            'location': LocationSerializer(wpl_1).data,
            'comment': wp_1.comment,
            'updated_by': wp_1.updated_by.id,
            'updated_on': date2iso(wp_1.updated_on)
        }
        self.assertDictEqual(wp_1_serializer.data, result)
        result = {
            'id': wpl_1.id,
            'type': LocationType.i.name,
            'location': point2str(wpl_1.location),
            'number': wpl_1.street,
            'street': wpl_1.street,
            'unit': wpl_1.unit,
            'neighborhood': wpl_1.neighborhood,
            'city': wpl_1.city,
            'state': wpl_1.state,
            'zipcode': wpl_1.zipcode,
            'country': wpl_1.country,
            'name': wpl_1.name,
            'comment': wpl_1.comment,
            'updated_by': wpl_1.updated_by.id,
            'updated_on': date2iso(wpl_1.updated_on)
        }
        self.assertDictEqual(wp_1_serializer.data['location'], result)

        wp_2_serializer = WaypointSerializer(wp_2)
        result = {
            'id': wp_2.id,
            'ambulance_call_id': ambulance_call_2.id,
            'order': 1,
            'status': WaypointStatus.D.name,
            'location': LocationSerializer(wpl_2).data,
            'comment': wp_2.comment,
            'updated_by': wp_2.updated_by.id,
            'updated_on': date2iso(wp_2.updated_on)
        }
        self.assertDictEqual(wp_2_serializer.data, result)
        result = {
            'id': wpl_2.id,
            'type': LocationType.h.name,
            'location': point2str(wpl_2.location),
            'number': '123',
            'street': 'adsasd',
            'unit': wpl_2.unit,
            'neighborhood': wpl_2.neighborhood,
            'city': wpl_2.city,
            'state': wpl_2.state,
            'zipcode': wpl_2.zipcode,
            'country': wpl_2.country,
            'name': wpl_2.name,
            'comment': wpl_2.comment,
            'updated_by': wpl_2.updated_by.id,
            'updated_on': date2iso(wpl_2.updated_on)
        }
        self.assertDictEqual(wp_2_serializer.data['location'], result)

        wp_3_serializer = WaypointSerializer(wp_3)
        result = {
            'id': wp_3.id,
            'ambulance_call_id': ambulance_call_2.id,
            'order': 2,
            'status': WaypointStatus.V.name,
            'location': LocationSerializer(self.h1).data,
            'comment': wp_3.comment,
            'updated_by': wp_3.updated_by.id,
            'updated_on': date2iso(wp_3.updated_on)
        }
        self.assertDictEqual(wp_3_serializer.data, result)
        result = {
            'id': self.h1.id,
            'type': LocationType.h.name,
            'location': point2str(self.h1.location),
            'number': self.h1.number,
            'street': self.h1.street,
            'unit': self.h1.unit,
            'neighborhood': self.h1.neighborhood,
            'city': self.h1.city,
            'state': self.h1.state,
            'zipcode': self.h1.zipcode,
            'country': self.h1.country,
            'name': self.h1.name,
            'comment': self.h1.comment,
            'updated_by': self.h1.updated_by.id,
            'updated_on': date2iso(self.h1.updated_on)
        }
        self.assertDictEqual(wp_3_serializer.data['location'], result)

        # add patients
        p1 = Patient.objects.create(call=c1, name='Jose', age=3)
        p2 = Patient.objects.create(call=c1, name='Maria', age=4)

        patient_serializer_1 = PatientSerializer(p1)
        patient_serializer_2 = PatientSerializer(p2)

        serializer = CallSerializer(c1)

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
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertCountEqual(serializer.data['ambulancecall_set'],
                              [ambulance_call_serializer_2.data, ambulance_call_serializer_1.data])
        self.assertCountEqual(serializer.data['patient_set'],
                              [patient_serializer_2.data, patient_serializer_1.data])
        result = serializer.data
        result['ambulancecall_set'] = []
        result['patient_set'] = []
        self.assertDictEqual(result, expected)

        # retrieve ambulance updates
        queryset = AmbulanceUpdate\
            .objects.filter(ambulance=self.a1.id)\
            .filter(timestamp__gte=ambulance_update_1.timestamp)\
            .exclude(id=ambulance_update_2.id)
        answer1 = []
        for u in queryset:
            serializer = AmbulanceUpdateSerializer(u)
            result = {
                'id': u.id,
                'ambulance_id': u.ambulance.id,
                'ambulance_identifier': u.ambulance.identifier,
                'comment': u.comment,
                'status': u.status,
                'orientation': u.orientation,
                'location': point2str(u.location),
                'timestamp': date2iso(u.timestamp),
                'updated_by_username': u.updated_by.username,
                'updated_on': date2iso(u.updated_on)
            }
            answer1.append(serializer.data)
        logger.debug(answer1)
        self.assertEqual(len(answer1), 2)

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve ambulances updates
        response = client.get('/en/api/ambulance/{}/updates/?call_id={}'.format(self.a1.id, c1.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        logger.debug(result)
        logger.debug(answer1)
        self.assertCountEqual(result, answer1)

        # logout
        client.logout()

        # cannot have duplicate
        # This must be last
        self.assertRaises(IntegrityError, AmbulanceCall.objects.create, call=c1, ambulance=self.a1, updated_by=self.u1)

    def test_call_serializer_create(self):

        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'ambulancecall_set': [],
            'patient_set': []
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # test CallSerializer
        c1 = Call.objects.get(id=call.id)
        serializer = CallSerializer(c1)

        result = {
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
            'ambulancecall_set': [],
            'patient_set': []
        }
        self.assertDictEqual(serializer.data, result)

        # accepted Call without Ambulancecall_Set fails
        call = {
            'status': CallStatus.S.name,
            'priority': CallPriority.B.name,
            'patient_set': []
        }
        serializer = CallSerializer(data=call)
        self.assertFalse(serializer.is_valid())

        # Pending Call with Ambulancecall_Set will create ambulancecalls
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
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
            'patient_set': []
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
            'priority_code': c1.priority_code,
            'radio_code': c1.radio_code,
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
        # logger.debug(result['ambulancecall_set'])
        # logger.debug(expected['ambulancecall_set'])
        self.assertCountEqual(result['ambulancecall_set'],
                              expected['ambulancecall_set'])
        expected['ambulancecall_set'] = []
        result['ambulancecall_set'] = []
        self.assertDictEqual(result, expected)

        # logger.debug(expected_ambulancecall_set[0])
        # logger.debug(expected_ambulancecall_set[1])

        self.assertEqual(len(expected_ambulancecall_set[0]['waypoint_set']), 2)
        self.assertEqual(len(expected_ambulancecall_set[1]['waypoint_set']), 1)

        # Pending Call with ambulancecall_set and patient_set
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a2.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # test CallSerializer
        c1 = Call.objects.get(id=call.id)

        serializer = CallSerializer(c1)

        expected_patient_set = PatientSerializer(Patient.objects.filter(call_id=c1.id), many=True).data
        expected_ambulancecall_set = AmbulanceCallSerializer(AmbulanceCall.objects.filter(call_id=c1.id), many=True).data

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
            'ambulancecall_set': expected_ambulancecall_set,
            'patient_set': expected_patient_set
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

        # Should fail because ambulance id's are repeated
        call = {
            'status': CallStatus.S.name,
            'priority': CallPriority.B.name,
            'ambulancecall_set': [{'ambulance_id': self.a1.id}, {'ambulance_id': self.a1.id}],
            'patient_set': []
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        self.assertRaises(IntegrityError, serializer.save, updated_by=self.u1)

        # make sure no call was created
        self.assertRaises(Call.DoesNotExist, Call.objects.get, status=CallStatus.S.name, priority=CallPriority.B.name)

    # THESE ARE FAILING!
    def _test_call_update_serializer(self):
        
        # superuser first

        # Update call status
        c = Call.objects.create(updated_by=self.u1)
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

        # # Update call street
        # street = 'new street'
        #
        # serializer = CallSerializer(c,
        #                             data={
        #                                 'street': street,
        #                             }, partial=True)
        # serializer.is_valid()
        # serializer.save(updated_by=user)
        #
        # # test
        # serializer = CallSerializer(c)
        # result = {
        #     'id': c.id,
        #     'status': c.status,
        #     'details': c.details,
        #     'priority': c.priority,
        #     'number': c.number,
        #     'street': street,
        #     'unit': c.unit,
        #     'neighborhood': c.neighborhood,
        #     'city': c.city,
        #     'state': c.state,
        #     'zipcode': c.zipcode,
        #     'country': c.country,
        #     'location': point2str(c.location),
        #     'created_at': date2iso(c.created_at),
        #     'pending_at': date2iso(c.pending_at),
        #     'started_at': date2iso(c.started_at),
        #     'ended_at': date2iso(c.ended_at),
        #     'comment': c.comment,
        #     'updated_by': c.updated_by.id,
        #     'updated_on': date2iso(c.updated_on),
        #     'ambulancecall_set': AmbulanceCallSerializer(many=True).data,
        #     'patient_set': PatientSerializer(many=True).data
        # }
        # self.assertDictEqual(serializer.data, result)
        #
        # # Update call location
        # location = {'latitude': -2., 'longitude': 7.}
        #
        # serializer = CallSerializer(c,
        #                             data={
        #                                 'location': location,
        #                             }, partial=True)
        # serializer.is_valid()
        # serializer.save(updated_by=user)
        #
        # # test
        # serializer = CallSerializer(c)
        # result = {
        #     'id': c.id,
        #     'status': c.status,
        #     'details': c.details,
        #     'priority': c.priority,
        #     'number': c.number,
        #     'street': c.street,
        #     'unit': c.unit,
        #     'neighborhood': c.neighborhood,
        #     'city': c.city,
        #     'state': c.state,
        #     'zipcode': c.zipcode,
        #     'country': c.country,
        #     'location': point2str(location),
        #     'created_at': date2iso(c.created_at),
        #     'pending_at': date2iso(c.pending_at),
        #     'started_at': date2iso(c.started_at),
        #     'ended_at': date2iso(c.ended_at),
        #     'comment': c.comment,
        #     'updated_by': c.updated_by.id,
        #     'updated_on': date2iso(c.updated_on),
        #     'ambulancecall_set': AmbulanceCallSerializer(many=True).data,
        #     'patient_set': PatientSerializer(many=True).data
        # }
        # self.assertDictEqual(serializer.data, result)

        # Need more tests for updates by regular authorized user

    def test_call_create_viewset(self):

        # instantiate client
        client = Client()
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        data = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
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
            'ambulancecall_set': expected_ambulancecall_set,
            'patient_set': expected_patient_set
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
            'ambulancecall_set': [{'ambulance_id': self.a3.id}, {'ambulance_id': self.a1.id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', data, content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 403)

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
