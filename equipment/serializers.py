from rest_framework import serializers

from .models import EquipmentItem, Equipment, EquipmentType


class EquipmentItemSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name')
    equipment_type = serializers.CharField(source='equipment.type')

    class Meta:
        model = EquipmentItem
        fields = ('equipmentholder_id',
                  'equipment_id', 'equipment_name', 'equipment_type',
                  'value', 'comment',
                  'updated_by', 'updated_on')
        read_only_fields = ('equipmentholder_id',
                            'equipment_id', 'equipment_name', 'equipment_type',
                            'updated_by',)



class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'