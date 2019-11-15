import logging

from import_export import resources

from ambulance.models import Ambulance, CallRadioCode, CallPriorityCode, CallPriorityClassification

logger = logging.getLogger(__name__)


class AmbulanceResource(resources.ModelResource):

    class Meta:
        model = Ambulance
        fields = ('id', 'identifier', 'capability', 'status',
                  'orientation', 'location', 'comment', 'active')
        export_order = ('id', 'identifier', 'capability', 'status',
                        'orientation', 'location', 'comment', 'active')


class CallRadioCodeResource(resources.ModelResource):

    class Meta:
        model = CallRadioCode
        fields = ('id', 'code', 'label')
        export_order = ('id', 'code', 'label')


class CallPriorityCodeResource(resources.ModelResource):

    class Meta:
        model = CallPriorityCode
        fields = ('id', 'prefix', 'priority', 'suffix', 'label')
        export_order = ('id', 'prefix', 'priority', 'suffix', 'label')


class CallPriorityClassificationResource(resources.ModelResource):

    class Meta:
        model = CallPriorityClassification
        fields = ('id', 'label')
        export_order = ('id', 'label')
