from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth.models import User, Group

from .models import Profile, GroupProfile


# Add signal to automatically extend user profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# Add signal to automatically extend group profile
@receiver(post_save, sender=Group)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        GroupProfile.objects.create(group=instance)
