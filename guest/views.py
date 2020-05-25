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
    template_name = 'video/index.html'



class VideoView(View):

    def get(self, request, sender_info=None):
        # username = receiver_info
        # password = 'top_sercret'
        # temp_user = User.objects.create_user(
        #         username=username,
        #         email='',
        #         password=password)
        # user_profile = UserProfile.objects.create(mobile_number=username,
        #         user=temp_user)
        # user_profile.is_guest = True
        # user_profile.save()

        # new_user = authenticate(username=username,
        #                             password=password,
        #                             )
        # login(request, new_user)
        
        # return HttpResponse(user_profile)

        username = 'guest'
        password = 'pandapanda'
        #authenticate user then login
        user = authenticate(username=username, password=password)
        login(request, user)
        

        response = redirect('/guest')
        return response

class RedirectView(View):
    def get(self, request, receiver_info=None):
        response = redirect('/')
        return response

