import logging

from import_export import resources

from ambulance.models import Ambulance

logger = logging.getLogger(__name__)


class AmbulanceResource(resources.ModelResource):

    class Meta:
        model = Ambulance
        fields = ('id', 'identifier', 'capability', 'status',
                  'orientation', 'location', 'active')
        export_order = ('id', 'identifier', 'capability', 'status',
                        'orientation', 'location', 'active')
