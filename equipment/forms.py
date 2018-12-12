from django import forms

from equipment.models import EquipmentHolder


class EquipmentHolderCreateForm(forms.ModelForm):

    class Meta:
        model = EquipmentHolder


class EquipmentHolderUpdateForm(EquipmentHolderCreateForm):
    pass
