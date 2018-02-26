from login.permissions import Permissions
from login.tests.setup_data import TestSetup


class TestPermissions(TestSetup):

    def test(self):

        u = self.u1
        perms = Permissions(u)
        self.assertEqual(len(perms['ambulances']), 1)
