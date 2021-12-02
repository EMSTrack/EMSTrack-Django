import logging
from django.views.generic.base import TemplateView
from rest_framework.authtoken.models import Token
import requests
import os
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)

class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        SERVER = "UCSD"
        param = {
            'username': os.environ["DASHBOARD_USERNAME_" + SERVER],
            'password': os.environ["DASHBOARD_PASSWORD_" + SERVER],
        }
        url = os.environ["DASHBOARD_AUTHURL_" + SERVER]
        res = requests.post(url, data=param)
        res.raise_for_status()
        token = res.json()['token']
        list_of_tokens = []
        list_of_users = []
        for user in User.objects.all():
            list_of_users.append(user)
            token_temp, created = Token.objects.get_or_create(user=user)
            list_of_tokens.append(token_temp.key)
        token_2, created = Token.objects.get_or_create(user=self.request.user)
        context['token'] = token_2.key
        context['username1'] = len(list_of_tokens)
        context['token_2'] = token # print the key
        context['username2'] = list_of_tokens[1]
        # print(list_of_users)
        # print(list_of_tokens)
        return context