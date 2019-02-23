import logging
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

logger = logging.getLogger(__name__)


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

    # default value for _loaded_values
    _loaded_values = None

    def __str__(self):
        return self.client_id

    def get_absolute_url(self):
        return reverse('login:detail-client', kwargs={'pk': self.id})

    @classmethod
    def from_db(cls, db, field_names, values):

        # call super
        instance = super(Client, cls).from_db(db, field_names, values)

        # store the original field values on the instance
        instance._loaded_values = dict(zip(field_names, values))

        # return instance
        return instance

    def save(self, *args, **kwargs):

        # creation?
        created = self.pk is None

        # loaded_values?
        loaded_values = self._loaded_values is not None

        # log
        log = []

        logger.debug('self = {}'.format(self))
        if loaded_values:
            logger.debug('_loaded_values = {}'.format(self._loaded_values))

        # online or reconnect
        if self.status == ClientStatus.O.name or self.status == ClientStatus.R.name:

            # log operation
            log.append({'client': self, 'status': self.status, 'activity': ClientActivity.HS.name})

            if self.status == ClientStatus.R.name and self.ambulance is None:

                try:

                    # retrieve latest ambulance logout
                    latest = ClientLog.objects.filter(status=ClientStatus.D.name,
                                                      activity=ClientActivity.AO.name).latest('updated_on')

                    identifier = latest.details
                    if identifier is not None:

                        # restore latest ambulance client
                        from ambulance.models import Ambulance
                        ambulance = Ambulance.objects.get(identifier=identifier)
                        self.ambulance = ambulance

                except ClientLog.DoesNotExist:
                    pass

            # ambulance login?
            if (self.ambulance is not None and
                    (not loaded_values or self._loaded_values['ambulance'] != self.ambulance)):

                # log ambulance login operation
                log.append({'client': self, 'status': ClientStatus.O.name,
                            'activity': ClientActivity.AI.name,
                            'details': self.ambulance.identifier})

            elif self.ambulance is None and loaded_values and self._loaded_values['ambulance'] is not None:

                # log ambulance logout operation
                log.append({'client': self, 'status': ClientStatus.O.name,
                            'activity': ClientActivity.AO.name,
                            'details': self._loaded_values['ambulance'].identifier})

            # hospital login?
            if (self.hospital is not None and
                    (not loaded_values or self._loaded_values['hospital'] != self.hospital)):

                # log hospital login operation
                log.append({'client': self, 'status': ClientStatus.O.name,
                            'activity': ClientActivity.HI.name,
                            'details': self.hospital.identifier})

            elif self.hospital is None and loaded_values and self._loaded_values['hospital'] is not None:

                # log hospital logout operation
                log.append({'client': self, 'status': ClientStatus.O.name,
                            'activity': ClientActivity.HO.name,
                            'details': self._loaded_values['hospital'].identifier})

        # offline or disconnected
        elif self.status == ClientStatus.D.name or self.status == ClientStatus.F.name:

            # has ambulance?
            if loaded_values and self._loaded_values['ambulance'] is not None:

                # log ambulance logout activity
                log.append({'client': self,
                            'status': self.status,
                            'activity': ClientActivity.AO.name,
                            'details': self._loaded_values['ambulance']})

            if self.ambulance is not None:

                # log warning
                logger.error("Client.save() called with status '{}' and ambulance '{} not None".format(self.status,
                                                                                                       self.ambulance))

                # logout ambulance
                self.ambulance = None

            # has hospital?
            if loaded_values and self._loaded_values['hospital'] is not None:
                # log hospital logout activity
                log.append({'client': self,
                            'status': self.status,
                            'activity': ClientActivity.HO.name,
                            'details': self._loaded_values['hospital']})

            if self.hospital is not None:
                # log warning
                logger.error("Client.save() called with status '{}' and hospital '{} not None".format(self.status,
                                                                                                       self.hospital))

                # logout hospital
                self.hospital = None

        # call super
        super().save(*args, **kwargs)

        # save logs
        for entry in log:
            logger.debug(entry)
            ClientLog.objects.create(**entry)


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
