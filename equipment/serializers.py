from rest_framework import serializers

from .models import EquipmentItem, Equipment


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

    # def validate(self, data):
    #     # call super
    #     validated_data = super().validate(data)
    #
    #     # TODO: validate equipment value using equipment_type
    #     return validated_data


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'