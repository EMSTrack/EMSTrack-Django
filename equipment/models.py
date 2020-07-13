from enum import Enum

from django.contrib.gis.db import models
from django import forms
from django.template.defaulttags import register
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from emstrack.models import UpdatedByModel, get_check
from emstrack.util import make_choices
from environs import Env

from equipment.widgets import StringCheckboxInput

env = Env()


@register.filter
def get_equipment_type(type_):
    return EquipmentType[type_].value


@register.filter(is_safe=True)
def get_equipment_value(value, type_):
    if type_ == EquipmentType.B.name:
        return get_check(value)
    else:
        return value


class EquipmentType(Enum):
    B = _('Boolean')
    I = _('Integer')
    S = _('String')


EquipmentTypeDefaults = {
    EquipmentType.B.name: "True",
    EquipmentType.I.name: "0",
    EquipmentType.S.name: ""
}


class Equipment(models.Model):
    name = models.CharField(_('name'), max_length=254, unique=True)

    type = models.CharField(_('type'), max_length=1,
                            choices=make_choices(EquipmentType))

    default = models.CharField(_('default'), blank=True, max_length=254)

    def save(self, *args, **kwargs):

        # set default value
        if not self.default:
            self.default = EquipmentTypeDefaults[self.type]

        # call super
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} ({})".format(self.name, self.type)

    def get_absolute_url(self, target='equipment:detail'):
        return reverse(target, kwargs={'pk': self.id})

    def get_value_widget(self):
        if self.type == EquipmentType.B.name:
            return StringCheckboxInput()
        elif self.type == EquipmentType.I.name:
            return forms.NumberInput()
        else: # elif type == EquipmentType.S.name:
            return forms.TextInput()


class EquipmentSet(models.Model):
    name = models.CharField(_('name'), max_length=254, unique=True)

    def get_absolute_url(self):
        return reverse('equipment:detail-set', kwargs={'pk': self.id})

    def __str__(self):
        return self.name


class EquipmentSetItem(models.Model):
    equipment_set = models.ForeignKey(EquipmentSet,
                                      on_delete=models.CASCADE,
                                      verbose_name=_('equipment_set'))
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE,
                                  verbose_name=_('equipment'))

    class Meta:
        unique_together = ('equipment_set', 'equipment',)


class EquipmentHolder(models.Model):

    equipmentsets = models.ManyToManyField(EquipmentSet, blank=True, verbose_name=_('equipmentsets'))

    def is_hospital(self):
        return hasattr(self, 'hospital')

    def is_ambulance(self):
        return hasattr(self, 'ambulance')

    def get_type(self):
        if self.is_hospital():
            return "hospital"
        elif self.is_ambulance():
            return "ambulance"
        return None

    def get_name(self):
        if self.is_hospital():
            return self.hospital.name
        elif self.is_ambulance():
            return self.ambulance.identifier
        return None

    def __str__(self):
        retval = "Equipment '{}'".format(self.id)
        if self.is_hospital():
            retval += ", Hospital '{}'".format(self.hospital)
        elif self.is_ambulance():
            retval += ", Ambulance '{}'".format(self.ambulance)
        else:
            retval += ", Unknown"
        return retval

    def get_absolute_url(self):
        if self.is_hospital():
            return reverse('hospital:detail', kwargs={'pk': self.hospital.id})
        elif self.is_ambulance():
            return reverse('ambulance:detail', kwargs={'pk': self.ambulance.id})
        else:
            return reverse('equipment:detail-holder', kwargs={'pk': self.id})


class EquipmentItem(UpdatedByModel):
    equipmentholder = models.ForeignKey(EquipmentHolder,
                                        on_delete=models.CASCADE,
                                        verbose_name=_('equipmentholder'))
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE,
                                  verbose_name=_('equipment'))
    value = models.CharField(_('value'), max_length=254)

    def save(self, *args, **kwargs):

        # creation?
        created = self.pk is None

        # if no value, set default value
        if not self.value:
            self.value = self.equipment.default

        # save to EquipmentItem
        super().save(*args, **kwargs)

        if env.bool("DJANGO_ENABLE_MQTT_PUBLISH", default=True):

            from mqtt.publish import SingletonPublishClient

            # publish to mqtt
            client = SingletonPublishClient()
            client.publish_equipment_item(self)

    class Meta:
        unique_together = ('equipmentholder', 'equipment',)

    def __str__(self):
        return "EquipmentHolder: {}, Equipment: {}, Count: {}".format(self.equipmentholder, self.equipment, self.value)
