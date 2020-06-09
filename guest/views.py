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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['video_openmodal'] = True
        context['video_call'] = None
        return context