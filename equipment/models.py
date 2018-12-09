from enum import Enum

from django.contrib.gis.db import models
from django.template.defaulttags import register
from django.urls import reverse

from emstrack.models import UpdatedByModel


class EquipmentType(Enum):
    B = 'Boolean'
    I = 'Integer'
    S = 'String'


class Equipment(models.Model):
    name = models.CharField(max_length=254, unique=True)

    EQUIPMENT_TYPE_CHOICES = \
        [(m.name, m.value) for m in EquipmentType]
    type = models.CharField(max_length=1,
                            choices=EQUIPMENT_TYPE_CHOICES)

    def __str__(self):
        return "{} ({})".format(self.name, self.type)

    def get_absolute_url(self):
        return reverse('equipment:detail', kwargs={'pk': self.id})


class EquipmentHolder(models.Model):
    pass


class EquipmentItem(UpdatedByModel):
    equipment_holder = models.ForeignKey(EquipmentHolder,
                                         on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE)
    value = models.CharField(max_length=254)

    def save(self, *args, **kwargs):

        # creation?
        created = self.pk is None

        # save to EquipmentItem
        super().save(*args, **kwargs)
        from mqtt.publish import SingletonPublishClient

        # publish to mqtt
        client = SingletonPublishClient()
        client.publish_equipment_item(self)
        if created:
            client.publish_equipment_metadata(self.equipment_holder)

    def delete(self, *args, **kwargs):

        # remove from mqtt
        from mqtt.publish import SingletonPublishClient
        client = SingletonPublishClient()
        client.remove_equipment_item(self)
        client.publish_equipment_metadata(self.equipment_holder)

        # delete from EquipmentItem
        super().delete(*args, **kwargs)

    class Meta:
        unique_together = ('equipment_holder', 'equipment',)

    def __str__(self):
        return "EquipmentHolder: {}, Equipment: {}, Count: {}".format(self.equipment_holder, self.equipment, self.value)


@register.filter
def get_equipment_type(type):
    return EquipmentType[type].value