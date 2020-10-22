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

    def validate(self, data):
        validated_data = super().validate(data)
        # Get what type of value is trying to be updated
        # print("Checking if value is integer value")
        status_of_val = ""
        str_search = True
        try:
            (validated_data['value'])
        except KeyError:
            return validated_data

        try:
            int(validated_data['value'])
            status_of_val = EquipmentType.I.name
            str_search = False
        except ValueError:
            str_search = True

        # ("Checking if value is string value")
        if (isinstance(validated_data['value'], str) and str_search and
                validated_data['value'] != 'False' and validated_data['value'] != 'True'):
            status_of_val = EquipmentType.S.name

        # ("Checking if value is boolean value False")
        if (validated_data['value'] == 'False') or (validated_data['value'] == 'True'):
            status_of_val = EquipmentType.B.name

        # printing info
        # print("Value of Updated Data in status_of_val either I S or B. " +
        #       validated_data['value'] + " is " + status_of_val)

        type_of_data = self.instance.equipment.type
        # print("Type of data itself: " + type_of_data)
        if status_of_val == EquipmentType.I.name and type_of_data != EquipmentType.I.name:
            # print("Trying to set non integer value to integer")
            raise serializers.ValidationError('Trying to set non integer value to integer')

        if status_of_val == EquipmentType.B.name and type_of_data != EquipmentType.B.name:
            # print("Trying to set non bool value to bool")
            raise serializers.ValidationError('Trying to set non bool value to bool')

        if status_of_val == EquipmentType.S.name and type_of_data != EquipmentType.S.name:
            # print("Trying to set non string value to string")
            raise serializers.ValidationError('Trying to set non string value to string')

        return validated_data


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'