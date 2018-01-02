from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver

from django.contrib.auth.models import User

from .models import Profile, Ambulance

# Add signal to automatically extend user profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Add signal to log ambulance location, status and comments to route
@receiver(pre_save, sender=Ambulance)
def add_to_route(sender, instance, **kwargs):
    pass

