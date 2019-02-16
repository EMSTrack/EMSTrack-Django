from enum import Enum

from django.contrib.gis.db import models

from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.validators import MinValueValidator
from django.template.defaulttags import register
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from emstrack.util import make_choices
from mqtt.cache_clear import mqtt_cache_clear


# filters

@register.filter
def get_client_status(key):
    return ClientStatus[key].value


@register.filter
def get_client_activity(key):
    return ClientActivity[key].value


@register.filter
def is_dispatcher(user):
    return user.is_superuser or user.is_staff or user.userprofile.is_dispatcher


class UserProfile(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                verbose_name=_('user'))
    is_dispatcher = models.BooleanField(_('is_dispatcher'), default=False)

    def get_absolute_url(self):
        return reverse('login:detail-user', kwargs={'pk': self.user.id})

    def __str__(self):
        return '{}'.format(self.user)

    def save(self, *args, **kwargs):

        # save to UserProfile
        super().save(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_profile(self.user)

    def delete(self, *args, **kwargs):

        # delete from UserProfile
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

        # remove from mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().remove_profile(self.user)


# GroupProfile

class GroupProfile(models.Model):
    group = models.OneToOneField(Group,
                                 on_delete=models.CASCADE,
                                 verbose_name=_('group'))

    description = models.CharField(_('description'), max_length=100, blank=True)
    priority = models.PositiveIntegerField(_('priority'), validators=[MinValueValidator(1)], default=10)

    def get_absolute_url(self):
        return reverse('login:detail-group', kwargs={'pk': self.group.id})

    def __str__(self):
        return '{}: description = {}'.format(self.group, self.description)

    class Meta:
        indexes = [models.Index(fields=['priority'])]

    def save(self, *args, **kwargs):

        # save to GroupProfile
        super().save(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

    def delete(self, *args, **kwargs):

        # delete from GroupProfile
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()


# Group Ambulance and Hospital Permissions

class Permission(models.Model):
    can_read = models.BooleanField(_('can_read'), default=True)
    can_write = models.BooleanField(_('can_write'), default=False)

    class Meta:
        abstract = True


class UserAmbulancePermission(Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name=_('user'))
    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE,
                                  verbose_name=_('ambulance'))

    class Meta:
        unique_together = ('user', 'ambulance')

    def save(self, *args, **kwargs):

        # save to UserAmbulancePermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_profile(self.user)

    def delete(self, *args, **kwargs):

        # delete from UserAmbulancePermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

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
                             on_delete=models.CASCADE,
                             verbose_name=_('user'))
    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE,
                                 verbose_name=_('hospital'))

    class Meta:
        unique_together = ('user', 'hospital')

    def save(self, *args, **kwargs):

        # save to UserHospitalPermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_profile(self.user)

    def delete(self, *args, **kwargs):

        # delete from UserHospitalPermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

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
                              on_delete=models.CASCADE,
                              verbose_name=_('group'))
    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE,
                                  verbose_name=_('ambulance'))

    class Meta:
        unique_together = ('group', 'ambulance')

    def save(self, *args, **kwargs):

        # save to GroupAmbulancePermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

        # update all profiles for users in the group
        for user in self.group.user_set.all():
            # publish to mqtt
            from mqtt.publish import SingletonPublishClient
            SingletonPublishClient().publish_profile(user)

    def delete(self, *args, **kwargs):

        # delete from GroupAmbulancePermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

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
                              on_delete=models.CASCADE,
                              verbose_name=_('group'))
    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE,
                                 verbose_name=_('hospital'))

    class Meta:
        unique_together = ('group', 'hospital')

    def save(self, *args, **kwargs):

        # save to GroupHospitalPermission
        super().save(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

        # update all profiles for users in the group
        for user in self.group.user_set.all():
            # publish to mqtt
            from mqtt.publish import SingletonPublishClient
            SingletonPublishClient().publish_profile(user)

    def delete(self, *args, **kwargs):

        # delete from GroupHospitalPermission
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

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
                                on_delete=models.CASCADE,
                                verbose_name=_('user'))
    password = models.CharField(_('password'), max_length=254)
    created_on = models.DateTimeField(_('created_on'), auto_now=True)

    def __str__(self):
        return '"{}" (created on: {})'.format(self.password, self.created_on)


# Client status
class ClientStatus(Enum):
    O = _('online')
    F = _('offline')
    D = _('disconnected')


# Client information
class Client(models.Model):

    # NOTE: This shouldn't be needed but django was giving me a hard time
    id = models.AutoField(_('id'), primary_key=True)

    # WARNING: mqtt client_id's can be up to 65536 bytes!
    client_id = models.CharField(_('client_id'), max_length=254, unique=True)

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name=_('user'))

    status = models.CharField(_('status'), max_length=1,
                              choices=make_choices(ClientStatus))

    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE,
                                  blank=True, null=True,
                                  verbose_name=_('ambulance'))

    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE,
                                 blank=True, null=True,
                                 verbose_name=_('hospital'))

    updated_on = models.DateTimeField(_('updated_on'), auto_now=True)

    def __str__(self):
        return self.client_id


# Client activity
class ClientActivity(Enum):
    HS = _('handshake')
    AI = _('ambulance login')
    AO = _('ambulance logout')
    TL = _('ambulance stop location')
    SL = _('ambulance start location')
    HI = _('hospital login')
    HO = _('hospital logout')


# Client log
class ClientLog(models.Model):

    client = models.ForeignKey(Client,
                               on_delete=models.CASCADE,
                               verbose_name=_('client'))

    status = models.CharField(_('status'), max_length=1,
                              choices=make_choices(ClientStatus))

    activity = models.CharField(_('activity'), max_length=2,
                                choices=make_choices(ClientActivity))

    details = models.CharField(_('details'), max_length=100, blank=True)

    updated_on = models.DateTimeField(_('updated_on'), auto_now=True)
