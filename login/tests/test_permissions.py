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
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_write_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_write_permission('ambulances',id))
        self.assertCountEqual(answer, perms.get_write_permissions('ambulances'))
        answer = [self.h1.id, self.h2.id]
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_read_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_read_permission('hospitals',id))
        self.assertCountEqual(answer, perms.get_read_permissions('hospitals'))
        answer = [self.h2.id]
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))

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
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))

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
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))

        u = self.u5
        perms = Permissions(u)
        self.assertEqual(3, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))
        answer = [self.a2.id, self.a3.id]
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_read_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_read_permission('ambulances',id))
        self.assertCountEqual(answer, perms.get_read_permissions('ambulances'))
        answer = [self.a2.id, self.a3.id]
        for id in all_ambulances:
            if id in answer:
                self.assertTrue(perms.check_write_permission('ambulances',id))
            else:
                self.assertFalse(perms.check_write_permission('ambulances',id))
        self.assertCountEqual(answer, perms.get_write_permissions('ambulances'))
        answer = [self.h1.id, self.h3.id]
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_read_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_read_permission('hospitals',id))
        self.assertCountEqual(answer, perms.get_read_permissions('hospitals'))
        answer = [self.h1.id]
        for id in all_hospitals:
            if id in answer:
                self.assertTrue(perms.check_write_permission('hospitals',id))
            else:
                self.assertFalse(perms.check_write_permission('hospitals',id))
        self.assertCountEqual(answer, perms.get_write_permissions('hospitals'))
