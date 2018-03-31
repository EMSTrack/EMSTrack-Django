from enum import Enum

from django.contrib.gis.db import models

from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.validators import MinValueValidator
from django.template.defaulttags import register
from django.urls import reverse

from login.permissions import cache_clear


# filters

@register.filter
def get_client_status(key):
    return ClientStatus[key].value


@register.filter
def get_client_activity(key):
    return ClientActivity[key].value


class UserProfile(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('login:user_detail', kwargs={'pk': self.user.id})

    def __str__(self):
        return '{}'.format(self.user)


# GroupProfile

class GroupProfile(models.Model):
    group = models.OneToOneField(Group,
                                 on_delete=models.CASCADE)

    description = models.CharField(max_length=100, blank=True, null=True)
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=10)

    def get_absolute_url(self):
        return reverse('login:group_detail', kwargs={'pk': self.group.id})

    def __str__(self):
        return '{}: description = {}'.format(self.group, self.description)

    class Meta:
        indexes = [models.Index(fields=['priority'])]


# Group Ambulance and Hospital Permissions

class Permission(models.Model):
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)

    class Meta:
        abstract = True


class UserAmbulancePermission(Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'ambulance')

    def save(self, *args, **kwargs):

        # save to UserAmbulancePermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_profile(self.user)

    def delete(self, *args, **kwargs):

        # delete from UserAmbulancePermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # publish to mqtt
        # does not remove because user still exists!
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_profile(self.user)

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.user,
                                                         self.ambulance.identifier,
                                                         self.ambulance.id,
                                                         self.can_read,
                                                         self.can_write)


class UserHospitalPermission(Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'hospital')

    def save(self, *args, **kwargs):

        # save to UserHospitalPermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_profile(self.user)

    def delete(self, *args, **kwargs):

        # delete from UserHospitalPermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # publish to mqtt
        # does not remove because user still exists!
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_profile(self.user)

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.user,
                                                         self.hospital.name,
                                                         self.hospital.id,
                                                         self.can_read,
                                                         self.can_write)


class GroupAmbulancePermission(Permission):
    group = models.ForeignKey(Group,
                              on_delete=models.CASCADE)
    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE)

    class Meta:
        unique_together = ('group', 'ambulance')

    def save(self, *args, **kwargs):

        # save to GroupAmbulancePermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # update all profiles for users in the group
        for user in self.group.user_set.all():
            # publish to mqtt
            from mqtt.publish import SingletonPublishClient
            SingletonPublishClient().publish_profile(user)

    def delete(self, *args, **kwargs):

        # delete from GroupAmbulancePermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # update all profiles for users in the group
        for user in self.group.user_set.all():
            # publish to mqtt
            from mqtt.publish import SingletonPublishClient
            SingletonPublishClient().publish_profile(user)

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.group,
                                                         self.ambulance.identifier,
                                                         self.ambulance.id,
                                                         self.can_read,
                                                         self.can_write)


class GroupHospitalPermission(Permission):
    group = models.ForeignKey(Group,
                              on_delete=models.CASCADE)
    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ('group', 'hospital')

    def save(self, *args, **kwargs):

        # save to GroupHospitalPermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # update all profiles for users in the group
        for user in self.group.user_set.all():
            # publish to mqtt
            from mqtt.publish import SingletonPublishClient
            SingletonPublishClient().publish_profile(user)

    def delete(self, *args, **kwargs):

        # delete from GroupHospitalPermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        cache_clear()

        # update all profiles for users in the group
        for user in self.group.user_set.all():
            # publish to mqtt
            from mqtt.publish import SingletonPublishClient
            SingletonPublishClient().publish_profile(user)

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.group,
                                                         self.hospital.name,
                                                         self.hospital.id,
                                                         self.can_read,
                                                         self.can_write)


# TemporaryPassword

class TemporaryPassword(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)
    password = models.CharField(max_length=254)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '"{}" (created on: {})'.format(self.password, self.created_on)


# Client status
class ClientStatus(Enum):
    O = 'online'
    F = 'offline'
    D = 'disconnected'


# Client information
class Client(models.Model):

    # NOTE: This shouldn't be needed but django was giving me a hard time
    id = models.AutoField(primary_key=True)

    # WARNING: mqtt client_id's can be up to 65536 bytes!
    client_id = models.CharField(max_length=254, unique=True)

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)

    CLIENT_STATUS_CHOICES = \
        [(m.name, m.value) for m in ClientStatus]
    status = models.CharField(max_length=1,
                              choices=CLIENT_STATUS_CHOICES)

    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE,
                                  blank=True, null=True)

    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE,
                                 blank=True, null=True)

    updated_on = models.DateTimeField(auto_now=True)


# Client activity
class ClientActivity(Enum):
    HS = 'handshake'
    AI = 'ambulance login'
    AO = 'ambulance logout'
    HI = 'hospital login'
    HO = 'hospital logout'


# Client log
class ClientLog(models.Model):

    client = models.ForeignKey(Client,
                               on_delete=models.CASCADE)

    status = models.CharField(max_length=1,
                              choices=Client.CLIENT_STATUS_CHOICES)

    CLIENT_ACTIVITIES_CHOICES = \
        [(m.name, m.value) for m in ClientActivity]
    activity = models.CharField(max_length=2,
                                choices=CLIENT_ACTIVITIES_CHOICES)

    details = models.CharField(max_length=100, blank=True, null=True)

    updated_on = models.DateTimeField(auto_now=True)
