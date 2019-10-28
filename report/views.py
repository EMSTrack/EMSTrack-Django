import logging

from django.conf import settings
from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _

from ambulance.models import LocationType, AmbulanceStatus

logger = logging.getLogger(__name__)


class ReportIndexView(TemplateView):
    template_name = 'report/index.html'


# Call DetailView
class VehicleReportView(TemplateView):
    template_name = 'report/vehicle.html'

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