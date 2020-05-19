import logging

from django.conf import settings
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.http import HttpResponse

from django.shortcuts import redirect

from login.models import UserProfile
logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = 'video/index.html'



class VideoView(View):

    def get(self, request, receiver_info=None):
        temp_user = User.objects.create_user(
                username=receiver_info,
                email='',
                password='top_secret')
        user_profile = UserProfile.objects.create(mobile_number=receiver_info,
                user=temp_user)
        user_profile.is_guest = True
        user_profile.save()
        return HttpResponse(user_profile)

        #response = redirect('/redirect-success/')
        #return response



