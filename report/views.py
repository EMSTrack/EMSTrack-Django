import logging

from django.views.generic.base import TemplateView

logger = logging.getLogger(__name__)


class ReportIndexView(TemplateView):
    template_name = 'report/index.html'


# Call DetailView
class VehicleReportView(TemplateView):
    template_name = 'report/vehicle.html'
