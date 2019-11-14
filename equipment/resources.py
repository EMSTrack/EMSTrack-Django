import logging

from import_export import resources, fields, widgets

from ambulance.models import Ambulance
from equipment.models import Equipment, EquipmentSet
from hospital.models import Hospital

logger = logging.getLogger(__name__)


class EquipmentResource(resources.ModelResource):

    class Meta:
        model = Equipment
        fields = ('id', 'name', 'type', 'default')
        export_order = ('id', 'name', 'type', 'default')


class EquipmentSetResource(resources.ModelResource):

    equipmentitem_set = fields.Field(attribute='equipmentitem_set',
                                     widget=widgets.ManyToManyWidget(Equipment, field='id', separator=','))

    class Meta:
        model = EquipmentSet
        fields = ('id', 'name', 'type', 'default')
        export_order = ('id', 'name', 'type', 'default')
