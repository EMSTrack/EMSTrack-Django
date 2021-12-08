from django.contrib.gis.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from ambulance.models import Location, LocationType
from equipment.models import EquipmentHolder
from environs import Env

env = Env()


# Hospital model

class Hospital(Location):

    equipmentholder = models.OneToOneField(EquipmentHolder,
                                           on_delete=models.CASCADE,
                                           verbose_name=_('equipmentholder'))

    # active
    active = models.BooleanField(_('active'), default=True)

    def save(self, *args, **kwargs):

        # creation?
        created = self.pk is None

        # create equipment holder?
        try:
            if created or self.equipmentholder is None:
                self.equipmentholder = EquipmentHolder.objects.create()
        except EquipmentHolder.DoesNotExist:
            self.equipmentholder = EquipmentHolder.objects.create()

        # enforce type hospital
        self.type = LocationType.h.name

        # save to Hospital
        super().save(*args, **kwargs)

        if env.bool("DJANGO_ENABLE_MQTT_PUBLISH", default=True):

            # publish to mqtt
            from mqtt.publish_client import SingletonPublishClient
            SingletonPublishClient().publish_hospital(self)

        # just created?
        if created:
            # invalidate permissions cache
            from mqtt.cache_clear import mqtt_cache_clear
            mqtt_cache_clear()

    def delete(self, *args, **kwargs):

        # invalidate permissions cache
        from mqtt.cache_clear import mqtt_cache_clear
        mqtt_cache_clear()

        # delete from Hospital
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('hospital:detail', kwargs={'pk': self.id})

    def __str__(self):
        return ('Hospital {}(id={})\n' +
                '   Comment: {}\n' +
                '   Updated: {} by {}').format(self.name,
                                               self.id,
                                               self.comment,
                                               self.updated_by,
                                               self.updated_on)
