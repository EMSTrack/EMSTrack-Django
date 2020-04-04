import logging
import os

from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from django.contrib.auth.models import User

from django.test import Client

from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestModels(TestSetup):

    def test_import(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # GET the import form
        response = client.get('/en/auth/user/import/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'import.html')
        self.assertContains(response, 'form action=""')

        # POST the import form
        input_format = '0'
        filename = os.path.join(
            os.path.dirname(__file__),
            os.path.pardir,
            'tests',
            'users.csv')
        with open(filename, "rb") as f:
            data = {
                'input_format': input_format,
                'import_file': f,
            }
            response = client.post('/en/auth/user/import/', data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)
        self.assertFalse(response.context['result'].has_errors())
        self.assertIn('confirm_form', response.context)
        confirm_form = response.context['confirm_form']

        data = confirm_form.initial
        self.assertEqual(data['original_file_name'], 'users.csv')
        response = client.post('/en/auth/user/process_import/', data,
                               follow=True)
        self.assertEqual(response.status_code, 200)

        users = Uers.objects.filter(username='newuser')
        self.assertTrue(users)

