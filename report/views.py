import logging
from django.views.generic.base import TemplateView

logger = logging.getLogger(__name__)


class ReportListView(TemplateView):
    template_name = 'report/index.html'