from enum import Enum

from django.urls import reverse
from django.contrib.gis.db import models
from django.template.defaulttags import register

from emstrack.models import AddressModel, UpdatedByModel


# filters
from login import permissions


@register.filter
def get_equipment_type(type):
    return EquipmentType[type].value


# Hospital model

class Hospital(AddressModel,
               UpdatedByModel):
    name = models.CharField(max_length=254, unique=True)

    def save(self, *args, **kwargs):

        # creation?
        created = self.pk is None

        # save to Hospital
        super().save(*args, **kwargs)

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_hospital(self)

        # just created?
        if created:
            # invalidate permissions cache
            permissions.cache_clear()

    def delete(self, *args, **kwargs):

        # remove from mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().remove_hospital(self)

        # invalidate permissions cache
        permissions.cache_clear()

        # delete from Hospital
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('hospital:detail', kwargs={'pk': self.id})

    def __str__(self):
        return ('Hospital {}(id={})\n' +
                '   Address: {} {} {}\n' +
                '            {} {} {}\n' +
                '            {} \n' +
                '  Location: {}\n' +
                '   Comment: {}\n' +
                '   Updated: {} by {}').format(self.name,
                                               self.id,
                                               self.number,
                                               self.street,
                                               self.unit,
                                               self.city,
                                               self.state,
                                               self.zipcode,
                                               self.country,
                                               self.location,
                                               self.comment,
                                               self.updated_by,
                                               self.updated_on)


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
        return reverse('hospital:equipment_detail', kwargs={'pk': self.id})


class HospitalEquipment(UpdatedByModel):
    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE)
    value = models.CharField(max_length=254)

    def save(self, *args, **kwargs):

        # creation?
        created = self.pk is None

        # save to HospitalEquipment
        super().save(*args, **kwargs)
        from mqtt.publish import SingletonPublishClient

        # publish to mqtt
        client = SingletonPublishClient()
        client.publish_hospital_equipment(self)
        if created:
            client.publish_hospital_metadata(self.hospital)

    def delete(self, *args, **kwargs):

        # remove from mqtt
        from mqtt.publish import SingletonPublishClient
        client = SingletonPublishClient()
        client.remove_hospital_equipment(self)
        client.publish_hospital_metadata(self.hospital)

        # delete from HospitalEquipment
        super().delete(*args, **kwargs)

    class Meta:
        unique_together = ('hospital', 'equipment',)

    def __str__(self):
        return "Hospital: {}, Equipment: {}, Count: {}".format(self.hospital, self.equipment, self.value)
