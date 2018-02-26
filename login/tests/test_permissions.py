from login.permissions import Permissions
from login.tests.setup_data import TestSetup


class TestPermissions(TestSetup):

    def test(self):

        u = self.u1
        perms = Permissions(u)
        self.assertEqual(1, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))
        answer = [self.a2.id]
        self.assertEqual(answer, perms.get_read_permissions('ambulances'))
        answer = [self.a2.id]
        self.assertEqual(answer, perms.get_write_permissions('ambulances'))
        answer = [self.h1.id, self.h3.id]
        self.assertEqual(answer, perms.get_read_permissions('hospitals'))
        answer = [self.h1.id]
        self.assertEqual(answer, perms.get_write_permissions('hospitals'))

        u = self.u2
        perms = Permissions(u)
        self.assertEqual(0, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))
        answer = []
        self.assertEqual(answer, perms.get_read_permissions('ambulances'))
        answer = []
        self.assertEqual(answer, perms.get_write_permissions('ambulances'))
        answer = [self.h1.id, self.h2.id]
        self.assertEqual(answer, perms.get_read_permissions('hospitals'))
        answer = [self.h2.id]
        self.assertEqual(answer, perms.get_write_permissions('hospitals'))

        u = self.u3
        perms = Permissions(u)
        self.assertEqual(2, len(perms.ambulances))
        self.assertEqual(0, len(perms.hospitals))
        answer = [self.a3.id]
        self.assertEqual(answer, perms.get_read_permissions('ambulances'))
        answer = [self.a3.id]
        self.assertEqual(answer, perms.get_write_permissions('ambulances'))
        answer = []
        self.assertEqual(answer, perms.get_read_permissions('hospitals'))
        answer = []
        self.assertEqual(answer, perms.get_write_permissions('hospitals'))

        u = self.u4
        perms = Permissions(u)
        self.assertEqual(0, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))

        u = self.u5
        perms = Permissions(u)
        self.assertEqual(3, len(perms.ambulances))
        self.assertEqual(2, len(perms.hospitals))
