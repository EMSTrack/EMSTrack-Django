from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Status, Ambulances, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, Route, Capability, LocationPoint, User


@receiver(post_delete, sender=Ambulances)
@receiver(post_save, sender=Ambulances)
def ambulances_mqtt_trigger(sender, **kwargs):
    # do mqtt transactions here
    print('Saved: {}'.format(kwargs['instance'].__dict__))
