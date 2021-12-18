import logging
from django.views.generic.base import TemplateView
from rest_framework.authtoken.models import Token
import requests
import os
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

logger = logging.getLogger(__name__)

class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # SERVER = "UCSD"
        # param = {
        #     'username': os.environ["DASHBOARD_USERNAME_" + SERVER],
        #     'password': os.environ["DASHBOARD_PASSWORD_" + SERVER],
        # }
        # url = os.environ["DASHBOARD_AUTHURL_" + SERVER]
        # res = requests.post(url, data=param)
        # res.raise_for_status()
        # token = res.json()['token']
        # list_of_tokens = []
        # list_of_users = []
        # for user in User.objects.all():
        #     list_of_users.append(user)
        #     token_temp, created = Token.objects.get_or_create(user=user)
        #     list_of_tokens.append(token_temp.key)
        # logger.error(list_of_users)
        # logger.error(list_of_tokens)
        # logger.error(self.request.user)
        # logger.error(list_of_users[1])
        # user = User.objects.get(username="admin")
        # logger.error(user)
        user = authenticate(username='admin', password='cruzrojaadmin')
        logger.error(user)
        user = user[0]
        token, created = Token.objects.get_or_create(user=user)
        context['token'] = token.key
        # context['token'] = self.request.META[]
        # context['username1'] = token_2.key
        # context['token_2'] = self.request.user.is_authenticated
        # context['username2'] = self.request.user.is_anonymous

        return context