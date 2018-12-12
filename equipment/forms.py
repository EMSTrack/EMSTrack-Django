from django import forms

from equipment.models import EquipmentHolder, EquipmentItem


class EquipmentItemForm(forms.ModelForm):

    class Meta:
        model = EquipmentItem
        fields = ['equipment', 'value', 'comment']


class EquipmentHolderCreateForm(forms.ModelForm):

    class Meta:
        model = EquipmentHolder
        fields = []


class EquipmentHolderUpdateForm(EquipmentHolderCreateForm):
    pass
