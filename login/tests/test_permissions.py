from login.permissions import Permissions
from login.tests.setup_data import TestSetup


class TestPermissions(TestSetup):

    def test(self):

        # superuser

        all_ambulances = set([self.a1.id, self.a2.id, self.a3.id])
        all_hospitals = set([self.h1.id, self.h2.id, self.h3.id])

        u = self.u1
        perms = Permissions(u)
        self.assertEqual(3, len(perms.ambulances))
        self.assertEqual(3, len(perms.hospitals))

        answer = [self.a1.id, self.a2.id, self.a3.id]
        self.assertCountEqual(answer, perms.get_read_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_read_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_read_permission('ambulances',id))
        self.assertCountEqual(answer, perms.get_write_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_write_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_write_permission('ambulances',id))

        answer = [self.h1.id, self.h2.id, self.h3.id]
        self.assertCountEqual(answer, perms.get_read_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_read_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_read_permission('hospitals',id))
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        answer = {
            'ambulances': {
                self.a1.id: {
                    'id': self.a1.id,
                    'can_read': True,
                    'can_write': True
                },
                self.a2.id: {
                    'id': self.a2.id,
                    'can_read': True,
                    'can_write': True
                },
                self.a3.id: {
                    'id': self.a3.id,
                    'can_read': True,
                    'can_write': True
                }
            },
            'hospitals': {
                self.h1.id: {
                    'id': self.h1.id,
                    'can_read': True,
                    'can_write': True
                },
                self.h2.id: {
                    'id': self.h2.id,
                    'can_read': True,
                    'can_write': True
                },
                self.h3.id: {
                    'id': self.h3.id,
                    'can_read': True,
                    'can_write': True
                }
            }
        }
        for id in all_ambulances:
            self.assertDictEqual(answer['ambulances'][id], perms.get_permissions('ambulances', id))
        for id in all_hospitals:
            self.assertDictEqual(answer['hospitals'][id], perms.get_permissions('hospitals', id))

        # regular users without groups

        u = self.u2
        perms = Permissions(u)
        self.assertEqual(0, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))
        answer = []
        self.assertCountEqual(answer, perms.get_read_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_read_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_read_permission('ambulances',id))
        answer = []
        self.assertCountEqual(answer, perms.get_write_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_write_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_write_permission('ambulances',id))
        answer = [self.h1.id, self.h2.id]
        self.assertCountEqual(answer, perms.get_read_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_read_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_read_permission('hospitals',id))
        answer = [self.h2.id]
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        answer = {
            'ambulances': {
            },
            'hospitals': {
                self.h1.id: {
                    'id': self.h1.id,
                    'can_read': True,
                    'can_write': False
                },
                self.h2.id: {
                    'id': self.h2.id,
                    'can_read': True,
                    'can_write': True
                },
            }
        }
        for id in all_ambulances:
            if id in answer['ambulances']:
                self.assertDictEqual(answer['ambulances'][id], perms.get_permissions('ambulances', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('ambulances', id)
        for id in all_hospitals:
            if id in answer['hospitals']:
                self.assertDictEqual(answer['hospitals'][id], perms.get_permissions('hospitals', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('hospitals', id)

        u = self.u3
        perms = Permissions(u)
        self.assertEqual(2, len(perms.ambulances))
        self.assertEqual(0, len(perms.hospitals))
        answer = [self.a3.id]
        self.assertCountEqual(answer, perms.get_read_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_read_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_read_permission('ambulances',id))
        answer = [self.a3.id]
        self.assertCountEqual(answer, perms.get_write_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_write_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_write_permission('ambulances',id))
        answer = []
        self.assertCountEqual(answer, perms.get_read_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_read_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_read_permission('hospitals',id))
        answer = []
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        answer = {
            'ambulances': {
                self.a3.id: {
                    'id': self.a3.id,
                    'can_read': True,
                    'can_write': True
                }
            },
            'hospitals': {
            }
        }
        for id in all_ambulances:
            if id in answer['ambulances']:
                self.assertDictEqual(answer['ambulances'][id], perms.get_permissions('ambulances', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('ambulances', id)
        for id in all_hospitals:
            if id in answer['hospitals']:
                self.assertDictEqual(answer['hospitals'][id], perms.get_permissions('hospitals', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('hospitals', id)

        # regular users with groups

        u = self.u4
        perms = Permissions(u)
        self.assertEqual(0, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))
        answer = []
        self.assertCountEqual(answer, perms.get_read_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_read_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_read_permission('ambulances',id))
        answer = []
        self.assertCountEqual(answer, perms.get_write_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_write_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_write_permission('ambulances',id))
        answer = [self.h1.id, self.h2.id]
        self.assertCountEqual(answer, perms.get_read_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_read_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_read_permission('hospitals',id))
        answer = [self.h2.id]
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        answer = {
            'ambulances': {
            },
            'hospitals': {
                self.h1.id: {
                    'id': self.h1.id,
                    'can_read': True,
                    'can_write': False
                },
                self.h2.id: {
                    'id': self.h2.id,
                    'can_read': True,
                    'can_write': True
                },
            }
        }
        for id in all_ambulances:
            if id in answer['ambulances']:
                self.assertDictEqual(answer['ambulances'][id], perms.get_permissions('ambulances', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('ambulances', id)
        for id in all_hospitals:
            if id in answer['hospitals']:
                self.assertDictEqual(answer['hospitals'][id], perms.get_permissions('hospitals', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('hospitals', id)

        u = self.u5
        perms = Permissions(u)
        self.assertEqual(3, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))
        answer = [self.a2.id, self.a3.id]
        self.assertCountEqual(answer, perms.get_read_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_read_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_read_permission('ambulances',id))
        answer = [self.a2.id, self.a3.id]
        self.assertCountEqual(answer, perms.get_write_permissions('ambulances'))
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_write_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_write_permission('ambulances',id))
        answer = [self.h1.id, self.h3.id]
        self.assertCountEqual(answer, perms.get_read_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_read_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_read_permission('hospitals',id))
        answer = [self.h1.id]
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        answer = {
            'ambulances': {
                self.a2.id: {
                    'id': self.a2.id,
                    'can_read': True,
                    'can_write': True
                },
                self.a3.id: {
                    'id': self.a3.id,
                    'can_read': True,
                    'can_write': True
                }
            },
            'hospitals': {
                self.h1.id: {
                    'id': self.h1.id,
                    'can_read': True,
                    'can_write': False
                },
                self.h3.id: {
                    'id': self.h3.id,
                    'can_read': True,
                    'can_write': True
                }
            }
        }
        for id in all_ambulances:
            if id in answer['ambulances']:
                self.assertDictEqual(answer['ambulances'][id], perms.get_permissions('ambulances', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('ambulances', id)
        for id in all_hospitals:
            if id in answer['hospitals']:
                self.assertDictEqual(answer['hospitals'][id], perms.get_permissions('hospitals', id))
            else:
                with self.assertRaise(KeyError):
                    perms.get_permissions('hospitals', id)
