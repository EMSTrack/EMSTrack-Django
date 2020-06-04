import logging

from django.conf import settings
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from django.http import HttpResponse

from django.shortcuts import redirect

from login.models import UserProfile
logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = 'guest/index.html'


class VideoView(View):

    def get(self, request, sender_info=None):
        username = 'guest'
        password = 'pandapanda'

        # authenticate user then login
        user = authenticate(username=username, password=password)
        login(request, user)
        
        response = redirect('/guest')
        return response


class RedirectView(View):

    def get(self, request, receiver_info=None):
        response = redirect('/')
        return response

