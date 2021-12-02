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
            list_of_tokens.append(token_temp)
        logger.error(list_of_users)
        logger.error(list_of_tokens)
        logger.error(self.request.user)
        logger.error(list_of_users[1])
        token_2 = Token.objects.get(id=self.request.user.id).key
        context['token'] = self.request.user.id
        context['username1'] = token_2
        context['token_2'] = self.request.user.is_authenticated
        context['username2'] = self.request.user.is_anonymous

        return context