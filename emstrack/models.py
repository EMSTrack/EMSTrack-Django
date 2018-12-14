from django.contrib.auth.models import User

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.template.defaulttags import register


# filters
from django.utils import timezone
from django.utils.safestring import mark_safe


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

    def get_address(self):
        address_str = '_'.join((self.number, self.street, self.unit))

        if address_str:
            address_str = ',*'.join((address_str, self.neighborhood))
        else:
            address_str = self.neighborhood

        if address_str:
            address_str = ',+'.join((address_str, self.city, self.state))
        else:
            address_str = ',-'.join((self.city, self.state))

        address_str = '@'.join((address_str, self.zipcode))
        address_str = ',%'.join((address_str, self.country))

        return address_str


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


