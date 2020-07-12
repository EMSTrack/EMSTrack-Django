from django import forms
from django.utils.translation import gettext_lazy as _

from djangoformsetjs.utils import formset_media_js

from equipment.models import Equipment, EquipmentHolder, EquipmentItem, EquipmentSetItem, EquipmentSet, EquipmentType


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


class EquipmentUpdateForm(forms.ModelForm):

    class Meta:
        model = Equipment
        fields = ['name', 'type', 'default']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs['instance']
        if instance is not None:
            type = instance.type
            if type == EquipmentType.B.name:
                self.fields.widgets['default'] = forms.CheckboxInput
            elif type == EquipmentType.I.name:
                self.fields.widgets['default'] = forms.NumberInput
            elif type == EquipmentType.S.name:
                self.fields.widgets['default'] = forms.TextInput
