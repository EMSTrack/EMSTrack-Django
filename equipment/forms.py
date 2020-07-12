from django import forms
from django.utils.translation import gettext_lazy as _

from djangoformsetjs.utils import formset_media_js

from equipment.models import EquipmentHolder, EquipmentItem, EquipmentSetItem, EquipmentSet


class EquipmentItemForm(forms.ModelForm):

    class Meta:
        model = EquipmentItem
        fields = ['equipment', 'value', 'comment']

    class Media(object):
        js = formset_media_js + (
            # Other form media here
        )


class EquipmentSetItemForm(forms.ModelForm):

    class Meta:
        model = EquipmentSetItem
        fields = ['equipment']

    class Media(object):
        js = formset_media_js + (
            # Other form media here
        )


class EquipmentSetCreateForm(forms.ModelForm):

    class Meta:
        model = EquipmentSet
        fields = ['name']


class EquipmentSetUpdateForm(EquipmentSetCreateForm):
    pass


class EquipmentHolderCreateForm(forms.ModelForm):

    class Meta:
        model = EquipmentHolder
        fields = ['equipmentsets']
        labels = {
            'equipmentsets': _('Equipment sets'),
        }


class EquipmentHolderUpdateForm(EquipmentHolderCreateForm):
    pass


class EquipmentForm(forms.ModelForm):

    default = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Equipment
        felds = ['name', 'type', 'default']
