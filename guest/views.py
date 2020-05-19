import logging

from django.conf import settings
from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from rest_framework.response import Response

from django.shortcuts import redirect

from login.models import UserProfile
logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = 'video/index.html'



class VideoView(TemplateView):

    def get(self, request, receiver_info=None):
        temp_user = User.objects.create_user(
                username=receiver_info,
                email='',
                password='top_secret')
        UserProfile.objects.create(is_guest=True, 
                mobile_number=receiver_info,
                user=temp_user)
        return Response(UserProfile)

        #response = redirect('/redirect-success/')
        #return response



