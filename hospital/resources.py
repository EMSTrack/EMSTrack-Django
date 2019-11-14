import logging

from import_export import resources

from ambulance.models import Ambulance
from hospital.models import Hospital

logger = logging.getLogger(__name__)


class HospitalResource(resources.ModelResource):

    class Meta:
        model = Hospital
        fields = ('id', 'name', 'type',
                  'number', 'street', 'unit', 'neighborhood', 'city', 'state', 'zipcode', 'country', 'location')
        export_order = ('id', 'name', 'type',
                        'number', 'street', 'unit', 'neighborhood', 'city', 'state', 'zipcode', 'country', 'location')
