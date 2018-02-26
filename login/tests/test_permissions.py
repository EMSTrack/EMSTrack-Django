from login.permissions import Permissions
from login.tests.setup_data import TestSetup


class TestPermissions(TestSetup):

    def test(self):

        u = self.u1
        perms = Permissions(u)
        self.assertEqual(len(perms.ambulances), 1)
        self.assertEqual(len(perms.hospitals), 2)

        u = self.u2
        perms = Permissions(u)
        self.assertEqual(len(perms.ambulances), 0)
        self.assertEqual(len(perms.hospitals), 2)

        u = self.u3
        perms = Permissions(u)
        self.assertEqual(len(perms.ambulances), 2)
        self.assertEqual(len(perms.hospitals), 0)

        u = self.u4
        perms = Permissions(u)
        self.assertEqual(len(perms.ambulances), 0)
        self.assertEqual(len(perms.hospitals), 2)

        u = self.u5
        perms = Permissions(u)
        self.assertEqual(len(perms.ambulances), 3)
        self.assertEqual(len(perms.hospitals), 2)
