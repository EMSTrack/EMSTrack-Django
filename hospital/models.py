from django.contrib.gis.db import models
from django.urls import reverse

from ambulance.models import Location, LocationType
from equipment.models import EquipmentHolder


# Hospital model

class Hospital(Location):

    equipmentholder = models.OneToOneField(EquipmentHolder,
                                           on_delete=models.CASCADE)

    def save(self, *args, **kwargs):

        # creation?
        created = self.pk is None

        # create equipment holder?
        if created and self.equipmentholder is None:
            self.equipmentholder = EquipmentHolder.objects.create()

        # enforce type hospital
        self.type = LocationType.h.name

        # save to Hospital
        super().save(*args, **kwargs)

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_hospital(self)

        # just created?
        if created:
            # invalidate permissions cache
            from login.permissions import cache_clear
            cache_clear()

    def delete(self, *args, **kwargs):

        # remove from mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().remove_hospital(self)

        # invalidate permissions cache
        from login.permissions import cache_clear
        cache_clear()

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


