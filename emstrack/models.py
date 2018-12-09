from enum import Enum

from django.contrib.auth.models import User

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.template.defaulttags import register


# filters
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from hospital.models import Hospital


@register.filter
def get_equipment_type(type):
    return EquipmentType[type].value


@register.filter(is_safe=True)
def get_check(key):
    if key:
        return mark_safe('<span class="fas fa-check"></span>')
    else:
        return ''


@register.filter(is_safe=True)
def get_times(key):
    if key:
        return ''
    else:
        return mark_safe('<span class="fas fa-times"></span>')


@register.filter(is_safe=True)
def get_check_or_times(key):
    if key:
        return mark_safe('<span class="fas fa-check"></span>')
    else:
        return mark_safe('<span class="fas fa-times"></span>')


defaults = {
    'location': Point(-117.0382, 32.5149, srid=4326),
    'state': 'BCN',
    'city': 'Tijuana',
    'country': 'MX',
}


class AddressModel(models.Model):
    """
    An abstract base class model that provides address fields.
    """

    number = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=254, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    neighborhood = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, default=defaults['city'])
    state = models.CharField(max_length=3, default=defaults['state'])
    zipcode = models.CharField(max_length=12, blank=True)
    country = models.CharField(max_length=2, default=defaults['country'])

    location = models.PointField(srid=4326, default=defaults['location'])

    class Meta:
        abstract = True


class UpdatedByModel(models.Model):
    """
    An abstract base class model that provides comments and update fields.
    """

    comment = models.CharField(max_length=254, blank=True)
    updated_by = models.ForeignKey(User,
                                   on_delete=models.CASCADE)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UpdatedByHistoryModel(models.Model):
    """
    An abstract base class model that provides comments and update fields.
    """

    comment = models.CharField(max_length=254, blank=True)
    updated_by = models.ForeignKey(User,
                                   on_delete=models.CASCADE)
    updated_on = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


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
