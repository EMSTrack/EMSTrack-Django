import json
import logging
from io import BytesIO

from django.contrib.auth import get_user_model
from rest_framework.parsers import JSONParser
from rest_framework.test import APIClient

from ambulance.models import CallStatus, CallPriority, Call, WaypointStatus
from ambulance.serializers import WaypointSerializer
from ambulance.models import LocationType

from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)
User = get_user_model()


class TestAmbulancewaypoint(TestSetup):

    def test_ambulancecall_waypoint_list_retrieve_viewset(self):

        # instantiate client
        client = APIClient()

        # login superuser
        user = User.objects.get(email='admin@user.com')
        client.force_authenticate(user=user)

        # create call
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'some street'
                            }
                        },
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                },
                                'type': LocationType.w.name,
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': self.a3.id,
                    'waypoint_set': [
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                },
                                'type': LocationType.w.name,
                            }
                        }
                    ]
                }
            ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', json.dumps(call), content_type='application/json')
        logger.debug(response.status_code)
        logger.debug(response.content)
        c1 = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(response.status_code, 201)

        # create call
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.A.name,
            'ambulancecall_set': [
                {
                    'ambulance_id': self.a2.id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '321',
                                'street': 'another street'
                            }
                        }
                    ]
                },
            ],
            'patient_set': [{'name': 'Maria', 'age': 3}, {'name': 'Jose'}]
        }
        response = client.post('/en/api/call/', json.dumps(call), content_type='application/json')
        c2 = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(response.status_code, 201)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a1.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 2)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a2.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a3.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 1)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a1.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a2.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 1)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a3.id))
        self.assertEqual(response.status_code, 404)

        # login as test2@user.com (DISPATCHER)
        user = User.objects.get(email='test2@user.com')
        client.force_authenticate(user=user)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a1.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 0)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a2.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a3.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 1)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a1.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a2.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 0)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a3.id))
        self.assertEqual(response.status_code, 404)

        # login as test1@user.com
        user = User.objects.get(email='test1@user.com')
        client.force_authenticate(user=user)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a1.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 0)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a2.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a3.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 0)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a1.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a2.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 0)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a3.id))
        self.assertEqual(response.status_code, 404)

        # login as test4@user.com
        user = User.objects.get(email='test4@user.com')
        client.force_authenticate(user=user)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a1.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 0)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a2.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c1['id'], self.a3.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 1)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a1.id))
        self.assertEqual(response.status_code, 404)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a2.id))
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(len(answer), 1)

        response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(c2['id'], self.a3.id))
        self.assertEqual(response.status_code, 404)

    def test_call_create_viewset_super(self):

        # instantiate client
        client = APIClient()

        # login superuser
        user = User.objects.get(email='admin@user.com')
        client.force_authenticate(user=user)

        # create call
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'some street'
                            }
                        },
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                },
                                'type': LocationType.w.name,
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '321',
                                'street': 'another street'
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': self.a3.id,
                }
            ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', json.dumps(call), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # call/+/ambulance/+/wapypoint list
        call = Call.objects.get(status=CallStatus.P.name)
        for ambulancecall in call.ambulancecall_set.all():

            response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, ambulancecall.ambulance.id))
            self.assertEqual(response.status_code, 200)
            answer = JSONParser().parse(BytesIO(response.content))
            expected = WaypointSerializer(ambulancecall.waypoint_set.all(), many=True).data
            self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/+/ retrieve
        for ambulancecall in call.ambulancecall_set.all():

            for waypoint in ambulancecall.waypoint_set.all():
                response = client.get('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, ambulancecall.ambulance.id, waypoint.id))
                self.assertEqual(response.status_code, 200)
                answer = JSONParser().parse(BytesIO(response.content))
                expected = WaypointSerializer(waypoint).data
                self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/ post
        data = {
            'order': 3,
            'location': {
                'location': {
                    'longitude': -123.0208,
                    'latitude': 44.0464
                },
                'type': LocationType.i.name,
                'number': '123',
                'street': 'some street'
            }
        }
        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a2.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a2).waypoint_set.last()).data
        self.assertCountEqual(answer, expected)

        data = {
            'location': {
                'location': {
                    'longitude': -123.0208,
                    'latitude': 44.0464
                },
                'type': LocationType.i.name,
                'number': '123',
                'street': 'some street'
            }
        }
        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a2.id),
                               json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 201)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a2).waypoint_set.last()).data
        logger.debug(answer)
        self.assertDictEqual(answer, expected)
        self.assertEqual(answer['order'], 4)

        data = {
            'location': {
                'location': {
                    'longitude': -123.0208,
                    'latitude': 44.0464
                },
                'type': LocationType.i.name,
                'number': '123',
                'street': 'some street'
            }
        }
        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a3.id),
                               json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 201)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a3).waypoint_set.last()).data
        self.assertDictEqual(answer, expected)
        self.assertEqual(answer['order'], 0)

        # call/+/ambulance/+/wapypoint/+/ update
        data = {
            'location': {
                'type': LocationType.w.name,
            }
        }
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a3.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a3).waypoint_set.last()).data
        logger.debug(answer)
        self.assertDictEqual(answer, expected)
        self.assertEqual(answer['location']['type'], LocationType.w.name)

        # call/+/ambulance/+/wapypoint/+/ update to forbidden type
        data = {
            'location': {
                'type': LocationType.h.name,
            }
        }
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a3.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 400)

    def test_call_create_viewset_privileged_user(self):

        # instantiate client
        client = APIClient()

        # login superuser
        user = User.objects.get(email='admin@user.com')
        client.force_authenticate(user=user)

        # create call
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'some street'
                            }
                        },
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                },
                                'type': LocationType.w.name,
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '321',
                                'street': 'another street'
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': self.a3.id,
                }
            ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', json.dumps(call), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # login as test2@user.com
        user = User.objects.get(email='test2@user.com')
        client.force_authenticate(user=user)

        # call/+/ambulance/+/wapypoint list
        call = Call.objects.get(status=CallStatus.P.name)
        for ambulancecall in call.ambulancecall_set.exclude(ambulance_id=self.a2.id):

            response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, ambulancecall.ambulance.id))
            self.assertEqual(response.status_code, 200)
            answer = JSONParser().parse(BytesIO(response.content))
            expected = WaypointSerializer(ambulancecall.waypoint_set.all(), many=True).data
            logger.debug("answer = %s", answer)
            logger.debug("expected = %s", expected)
            self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/+/ retrieve
        for ambulancecall in call.ambulancecall_set.all():

            for waypoint in ambulancecall.waypoint_set.all():
                response = client.get('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, ambulancecall.ambulance.id, waypoint.id))
                self.assertEqual(response.status_code, 200)
                answer = JSONParser().parse(BytesIO(response.content))
                expected = WaypointSerializer(waypoint).data
                self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/ post
        data = {
            'order': 3,
            'location': {
                'location': {
                    'longitude': -123.0208,
                    'latitude': 44.0464
                },
                'type': LocationType.i.name,
                'number': '123',
                'street': 'some street'
            }
        }
        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a2.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a3.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a1.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a1).waypoint_set.last()).data
        self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/+/ update
        data = {
            'location': {
                'type': LocationType.w.name,
            }
        }
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a2.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 404)

        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a3.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 404)

        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a1.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a1).waypoint_set.last()).data
        logger.debug(answer)
        self.assertDictEqual(answer, expected)
        self.assertEqual(answer['location']['type'], LocationType.w.name)

        # call/+/ambulance/+/wapypoint/+/ update to forbidden type
        data = {
            'location': {
                'type': LocationType.h.name,
            }
        }
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a1.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 400)

    def test_call_create_viewset_unprivileged_user(self):

        # instantiate client
        client = APIClient()

        # login superuser
        user = User.objects.get(email='admin@user.com')
        client.force_authenticate(user=user)

        # create call
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'some street'
                            }
                        },
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                },
                                'type': LocationType.w.name,
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '321',
                                'street': 'another street'
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': self.a3.id,
                }
            ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', json.dumps(call), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # login as test2@user.com
        user = User.objects.get(email='test1@user.com')
        client.force_authenticate(user=user)

        # call/+/ambulance/+/wapypoint list
        call = Call.objects.get(status=CallStatus.P.name)
        for ambulancecall in call.ambulancecall_set.all():

            response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, ambulancecall.ambulance.id))
            self.assertEqual(response.status_code, 200)
            answer = JSONParser().parse(BytesIO(response.content))
            expected = []
            self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/+/ retrieve
        for ambulancecall in call.ambulancecall_set.all():

            for waypoint in ambulancecall.waypoint_set.all():
                response = client.get('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, ambulancecall.ambulance.id, waypoint.id))
                self.assertEqual(response.status_code, 404)

        # call/+/ambulance/+/wapypoint/ post
        data = {
            'order': 3,
            'location': {
                'location': {
                    'longitude': -123.0208,
                    'latitude': 44.0464
                },
                'type': LocationType.i.name,
                'number': '123',
                'street': 'some street'
            }
        }
        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a2.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a3.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a1.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        # call/+/ambulance/+/wapypoint/+/ update
        data = {
            'location': {
                'type': LocationType.w.name,
            }
        }
        waypoint = call.ambulancecall_set.get(ambulance=self.a2.id).waypoint_set.last()
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a2.id, waypoint.id),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 404)

        waypoint = call.ambulancecall_set.get(ambulance=self.a1.id).waypoint_set.last()
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a1.id, waypoint.id),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 404)

    def test_call_create_viewset_dispatcher(self):

        # instantiate client
        client = APIClient()

        # login superuser
        user = User.objects.get(email='admin@user.com')
        client.force_authenticate(user=user)

        # create call
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'some street'
                            }
                        },
                        {
                            'order': 1,
                            'status': WaypointStatus.D.name,
                            'location': {
                                'location': {
                                    'longitude': -110.54,
                                    'latitude': 35.75
                                },
                                'type': LocationType.w.name,
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
                                'location': {
                                    'longitude': -123.0208,
                                    'latitude': 44.0464
                                },
                                'type': LocationType.i.name,
                                'number': '321',
                                'street': 'another street'
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': self.a3.id,
                }
            ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        response = client.post('/en/api/call/', json.dumps(call), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # login as test2@user.com
        user = User.objects.get(email='test4@user.com')
        client.force_authenticate(user=user)

        # call/+/ambulance/+/wapypoint list
        call = Call.objects.get(status=CallStatus.P.name)
        for ambulance in [self.a2, self.a3]:

            ambulancecall = call.ambulancecall_set.get(ambulance=ambulance)
            response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, ambulancecall.ambulance.id))
            self.assertEqual(response.status_code, 200)
            answer = JSONParser().parse(BytesIO(response.content))
            expected = WaypointSerializer(ambulancecall.waypoint_set.all(), many=True).data
            self.assertCountEqual(answer, expected)

        for ambulance in [self.a1]:

            ambulancecall = call.ambulancecall_set.get(ambulance=ambulance)
            response = client.get('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, ambulancecall.ambulance.id))
            self.assertEqual(response.status_code, 200)
            answer = JSONParser().parse(BytesIO(response.content))
            expected = []
            self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/+/ retrieve
        for ambulance in [self.a2, self.a3]:
            for waypoint in call.ambulancecall_set.get(ambulance=ambulance).waypoint_set.all():
                response = client.get('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, ambulance.id, waypoint.id))
                self.assertEqual(response.status_code, 200)
                answer = JSONParser().parse(BytesIO(response.content))
                expected = WaypointSerializer(waypoint).data
                self.assertCountEqual(answer, expected)

        for ambulance in [self.a1]:
            for waypoint in call.ambulancecall_set.get(ambulance=ambulance).waypoint_set.all():
                response = client.get('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, ambulance.id, waypoint.id))
                self.assertEqual(response.status_code, 404)

        # call/+/ambulance/+/wapypoint/ post
        data = {
            'order': 3,
            'location': {
                'location': {
                    'longitude': -123.0208,
                    'latitude': 44.0464
                },
                'type': LocationType.i.name,
                'number': '123',
                'street': 'some street'
            }
        }
        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a1.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a3.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        response = client.post('/en/api/call/{}/ambulance/{}/waypoint/'.format(call.id, self.a2.id),
                               json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a2).waypoint_set.last()).data
        self.assertCountEqual(answer, expected)

        # call/+/ambulance/+/wapypoint/+/ update
        data = {
            'location': {
                'type': LocationType.w.name,
            }
        }
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a1.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 404)

        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a3.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 404)

        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a2.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 200)
        answer = JSONParser().parse(BytesIO(response.content))
        expected = WaypointSerializer(call.ambulancecall_set.get(ambulance=self.a2).waypoint_set.last()).data
        logger.debug(answer)
        self.assertDictEqual(answer, expected)
        self.assertEqual(answer['location']['type'], LocationType.w.name)

        # call/+/ambulance/+/wapypoint/+/ update to forbidden type
        data = {
            'location': {
                'type': LocationType.h.name,
            }
        }
        response = client.patch('/en/api/call/{}/ambulance/{}/waypoint/{}/'.format(call.id, self.a2.id, answer['id']),
                                json.dumps(data), content_type='application/json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 400)
