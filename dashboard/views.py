import logging

from django.views.generic.base import TemplateView

logger = logging.getLogger(__name__)

class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'
