from enum import Enum

from django.utils import timezone
from django.urls import reverse

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

from emstrack.models import AddressModel, UpdatedByModel

# Hospital model
    
class Hospital(AddressModel,
               UpdatedByModel):
    
    name = models.CharField(max_length=254, unique=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) 
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_hospital(self)

    def delete(self, *args, **kwargs):
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().remove_hospital(self)
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('hospital:detail', kwargs={'pk': self.id})
        
    def __str__(self):
        return ('> Hospital {}(id={})\n' +
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

    EQUIPMENT_ETYPE_CHOICES = \
        [(m.name, m.value) for m in EquipmentType]
    etype = models.CharField(max_length=1,
                             choices = EQUIPMENT_ETYPE_CHOICES)
    
    toggleable = models.BooleanField(default=False)

    def __str__(self):
        return "{} ({})".format(self.name, self.etype)


class HospitalEquipment(UpdatedByModel):

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment,
                                  on_delete=models.CASCADE)
    value = models.CharField(max_length=254)
    
    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs) 
        from mqtt.publish import SingletonPublishClient
        client = SingletonPublishClient()
        client.publish_hospital_equipment(self)
        if created:
            client.publish_hospital_metadata(self.hospital)

    def delete(self, *args, **kwargs):
        from mqtt.publish import SingletonPublishClient
        client = SingletonPublishClient()
        client.remove_hospital_equipment(self)
        client.publish_hospital_metadata(self.hospital)
        super().delete(*args, **kwargs)
        
    class Meta:
        unique_together = ('hospital', 'equipment',)

    def __str__(self):
        return "Hospital: {}, Equipment: {}, Count: {}".format(self.hospital, self.equipment, self.value)

