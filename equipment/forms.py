from django import forms

from djangoformsetjs.utils import formset_media_js

from equipment.models import EquipmentHolder, EquipmentItem


class EquipmentItemForm(forms.ModelForm):

    class Meta:
        model = EquipmentItem
        fields = ['equipment', 'value', 'comment']

    class Media(object):
        js = formset_media_js + (
            # Other form media here
        )


class EquipmentHolderCreateForm(forms.ModelForm):

    class Meta:
        model = EquipmentHolder
        fields = []


class EquipmentHolderUpdateForm(EquipmentHolderCreateForm):
    pass
