import logging
from django import forms
from django.utils.translation import gettext_lazy as _

from djangoformsetjs.utils import formset_media_js

from equipment.models import Equipment, EquipmentHolder, EquipmentItem, EquipmentSetItem, EquipmentSet, EquipmentType

logger = logging.getLogger(__name__)


class EquipmentItemForm(forms.ModelForm):

    class Meta:
        model = EquipmentItem
        fields = ['equipment', 'value', 'comment']

    class Media(object):
        js = formset_media_js + (
            # Other form media here
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance is not None:
            self.fields['value'].widget = instance.equipment.get_value_widget()
            self.fields['equipment'].disabled = True


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
    equipmentsets = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                   queryset=EquipmentSet.objects.all(),
                                                   required=False)

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
        instance = kwargs.get('instance')
        if instance is not None:
            self.fields['default'].widget = instance.get_value_widget()
            self.fields['type'].disabled = True
