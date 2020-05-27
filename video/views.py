import logging

from django.conf import settings
from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = 'video/index.html'
