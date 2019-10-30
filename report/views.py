import logging

from django.conf import settings
from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _

from ambulance.models import LocationType, AmbulanceStatus
from ambulance.views import AmbulanceCSS

logger = logging.getLogger(__name__)


class ReportIndexView(TemplateView):
    template_name = 'report/index.html'


# Vehicle Mileage Report
class VehicleMileageReportView(TemplateView):
    template_name = 'report/vehicle-mileage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location_type'] = {m.name: m.value
                                    for m in LocationType}
        context['ambulance_status'] = {m.name: m.value
                                       for m in AmbulanceStatus}
        context['map_provider'] = {'provider': settings.MAP_PROVIDER,
                                   'access_token': settings.MAP_PROVIDER_TOKEN}

        context['translation_table'] = {
            "Abort Call": _("Abort Call"),
            "Are you sure?": _("Are you sure?"),
        }

        return context


# Vehicle Status Report
class VehicleStatusReportView(TemplateView):
    template_name = 'report/vehicle-status.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location_type'] = {m.name: m.value
                                    for m in LocationType}
        context['ambulance_status'] = {m.name: m.value
                                       for m in AmbulanceStatus}
        context['map_provider'] = {'provider': settings.MAP_PROVIDER,
                                   'access_token': settings.MAP_PROVIDER_TOKEN}
        context['ambulance_css'] = AmbulanceCSS

        context['translation_table'] = {
            "Abort Call": _("Abort Call"),
            "Are you sure?": _("Are you sure?"),
        }

        return context

