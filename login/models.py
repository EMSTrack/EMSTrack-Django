from enum import Enum

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.validators import MinValueValidator
from django.template.defaulttags import register
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from emstrack.util import make_choices
from login.mixins import ClearPermissionCacheMixin


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


class UserProfile(ClearPermissionCacheMixin,
                  models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                verbose_name=_('user'))
    is_dispatcher = models.BooleanField(_('is_dispatcher'), default=False)

    def get_absolute_url(self):
        return reverse('login:detail-user', kwargs={'pk': self.user.id})

    def __str__(self):
        return '{}'.format(self.user)


# GroupProfile

class GroupProfile(ClearPermissionCacheMixin,
                   models.Model):
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


# Group Ambulance and Hospital Permissions

class Permission(models.Model):
    can_read = models.BooleanField(_('can_read'), default=True)
    can_write = models.BooleanField(_('can_write'), default=False)

    class Meta:
        abstract = True


class UserAmbulancePermission(ClearPermissionCacheMixin,
                              Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name=_('user'))
    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE,
                                  verbose_name=_('ambulance'))

    class Meta:
        unique_together = ('user', 'ambulance')

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.user,
                                                         self.ambulance.identifier,
                                                         self.ambulance.id,
                                                         self.can_read,
                                                         self.can_write)


class UserHospitalPermission(ClearPermissionCacheMixin,
                             Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name=_('user'))
    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE,
                                 verbose_name=_('hospital'))

    class Meta:
        unique_together = ('user', 'hospital')

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.user,
                                                         self.hospital.name,
                                                         self.hospital.id,
                                                         self.can_read,
                                                         self.can_write)


class GroupAmbulancePermission(ClearPermissionCacheMixin,
                               Permission):
    group = models.ForeignKey(Group,
                              on_delete=models.CASCADE,
                              verbose_name=_('group'))
    ambulance = models.ForeignKey('ambulance.Ambulance',
                                  on_delete=models.CASCADE,
                                  verbose_name=_('ambulance'))

    class Meta:
        unique_together = ('group', 'ambulance')

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.group,
                                                         self.ambulance.identifier,
                                                         self.ambulance.id,
                                                         self.can_read,
                                                         self.can_write)


class GroupHospitalPermission(ClearPermissionCacheMixin,
                              Permission):
    group = models.ForeignKey(Group,
                              on_delete=models.CASCADE,
                              verbose_name=_('group'))
    hospital = models.ForeignKey('hospital.Hospital',
                                 on_delete=models.CASCADE,
                                 verbose_name=_('hospital'))

    class Meta:
        unique_together = ('group', 'hospital')

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
    R = _('reconnected')


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

    ambulance = models.OneToOneField('ambulance.Ambulance',
                                     on_delete=models.CASCADE,
                                     blank=True, null=True,
                                     verbose_name=_('ambulance'))

    hospital = models.OneToOneField('hospital.Hospital',
                                    on_delete=models.CASCADE,
                                    blank=True, null=True,
                                    verbose_name=_('hospital'))

    updated_on = models.DateTimeField(_('updated_on'), auto_now=True)

    def __str__(self):
        return self.client_id

    def get_absolute_url(self):
        return reverse('login:detail-client', kwargs={'pk': self.id})


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
