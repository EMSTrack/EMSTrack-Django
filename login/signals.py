from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from django.contrib.auth.models import User, Group

from mqtt.cache_clear import mqtt_cache_clear
from .models import UserProfile, GroupProfile


# Add signal to automatically clear cache when group permissions change
@receiver(m2m_changed, sender=User.groups.through)
def user_groups_changed_handler(sender, instance, action, **kwargs):
    if action == 'post_add' or action == 'post_remove':

        # invalidate permissions cache
        mqtt_cache_clear()


# Add signal to automatically extend group profile
@receiver(post_save, sender=Group)
def create_group_profile(sender, instance, created, **kwargs):
    if created:
        GroupProfile.objects.create(group=instance)


# Add signal to automatically extend user profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
