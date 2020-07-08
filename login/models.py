import logging
import random
import string

from datetime import timedelta

from enum import Enum

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.exceptions import PermissionDenied
from django.core.validators import MinValueValidator, RegexValidator
from django.template.defaulttags import register
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify

from phonenumber_field.modelfields import PhoneNumberField

from ambulance.models import AmbulanceStatus
from emstrack.util import make_choices
from login.mixins import ClearPermissionCacheMixin
from login.permissions import get_permissions

from environs import Env

env = Env()
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


@register.filter
def is_guest(user):
    return user.userprofile.is_guest
    

class UserProfile(ClearPermissionCacheMixin,
                  models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                verbose_name=_('user'))
    is_dispatcher = models.BooleanField(_('is_dispatcher'), default=False)
    is_guest = models.BooleanField(_('is_guest'), default=False)
    mobile_number = PhoneNumberField(blank=True)

    def get_absolute_url(self):
        return reverse('login:detail-user', kwargs={'pk': self.user.id})

    def __str__(self):
        return '{}'.format(self.user)


# GroupProfile

def can_sms_notifications():
    groups = Group.objects.filter(groupprofile__can_sms_notifications=True).prefetch_related('user_set')
    users = [g.user_set.all() for g in groups]
    n = len(users)
    if n > 1:
        # union of all groups
        users = users[0].union(users[1:])
    elif n == 1:
        # just one group
        users = users[0]
    else:
        # none
        users = User.objects.none()
    return users


class GroupProfile(ClearPermissionCacheMixin,
                   models.Model):
    group = models.OneToOneField(Group,
                                 on_delete=models.CASCADE,
                                 verbose_name=_('group'))

    description = models.CharField(_('description'), max_length=100, blank=True)
    priority = models.PositiveIntegerField(_('priority'), validators=[MinValueValidator(1)], default=10)
    can_sms_notifications = models.BooleanField(_('can_sms_notifications'), default=False)

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

    def get_absolute_url(self):
        return reverse('login:detail-group', kwargs={'pk': self.group.id})

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

    def get_absolute_url(self):
        return reverse('login:detail-group', kwargs={'pk': self.group.id})

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.group,
                                                         self.hospital.name,
                                                         self.hospital.id,
                                                         self.can_read,
                                                         self.can_write)


# random string
def random_string_generator(size=20,
                            chars=(string.ascii_letters +
                                   string.digits +
                                   string.punctuation)):
    return ''.join(random.choice(chars) for _ in range(size))


# TokenLogin

def unique_slug_generator(new_slug=None):
    # generate slug
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(random_string_generator(size=50,
                                               chars=(string.ascii_letters +
                                                      string.digits)))

    # if exists, try again
    if TokenLogin.objects.filter(token=slug).exists():
        return unique_slug_generator(new_slug=random_string_generator(size=50,
                                                                      chars=(string.ascii_letters +
                                                                             string.digits)))
    return slug


class TokenLogin(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    token = models.SlugField(max_length=50,
                             default=unique_slug_generator,
                             unique=True,
                             null=False)
    url = models.URLField(max_length=512, null=True, blank=True)
    created_on = models.DateTimeField(_('created_on'),
                                      auto_now=True)


# TemporaryPassword

class TemporaryPassword(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                verbose_name=_('user'))
    password = models.CharField(_('password'), max_length=254)
    created_on = models.DateTimeField(_('created_on'), auto_now=True)

    def __str__(self):
        return '"{}" (created on: {})'.format(self.password, self.created_on)

    @staticmethod
    def get_or_create_password(user):

        try:

            # Retrieve current password
            pwd = TemporaryPassword.objects.get(user=user)
            password = pwd.password
            valid_until = pwd.created_on + timedelta(seconds=120)

            # Invalidate password if it is expired
            if timezone.now() > valid_until:
                password = None

        except TemporaryPassword.DoesNotExist:

            pwd = None
            password = None

        if password is None:

            # Generate password
            password = random_string_generator()

            if pwd is None:

                # create password
                pwd = TemporaryPassword(user=user,
                                        password=password)

            else:

                # update password
                pwd.password = password

            # save password
            pwd.save()

        return pwd


# Client status
class ClientStatus(Enum):
    O = _('online')
    F = _('offline')
    D = _('disconnected')
    R = _('reconnected')


# Client information
class Client(models.Model):

    # NOTE: This shouldn't be needed but django was giving me a hard time
    # id = models.AutoField(_('id'), primary_key=True)

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
        return '{}[{},{}](ambulance={},hospital={})'.format(self.client_id, self.status,
                                                            self.user, self.ambulance, self.hospital)

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

        from ambulance.models import Ambulance
        from hospital.models import Hospital

        # creation?
        created = self.pk is None

        # loaded_values?
        loaded_values = self._loaded_values is not None

        # log
        log = []

        # publication list
        publish_ambulance = set()
        publish_hospital = set()

        # logger.debug('self = {}'.format(self))
        # if loaded_values:
        #     logger.debug('_loaded_values = {}'.format(self._loaded_values))

        # online or reconnect
        if self.status == ClientStatus.O.name or self.status == ClientStatus.R.name:

            # log operation
            log.append({'client': self, 'user': self.user, 'status': self.status, 'activity': ClientActivity.HS.name})

            if self.status == ClientStatus.R.name and self.ambulance is None:

                try:

                    # retrieve latest ambulance logout
                    latest = ClientLog.objects.filter(status=ClientStatus.D.name,
                                                      activity=ClientActivity.AO.name).latest('updated_on')

                    identifier = latest.details
                    if identifier is not None:

                        # restore latest ambulance client
                        ambulance = Ambulance.objects.get(identifier=identifier)
                        self.ambulance = ambulance

                except ClientLog.DoesNotExist:
                    pass

            # last ambulance
            if loaded_values and self._loaded_values['ambulance_id'] is not None:
                last_ambulance = Ambulance.objects.get(id=self._loaded_values['ambulance_id'])
            else:
                last_ambulance = None

            # changed ambulance?
            if last_ambulance != self.ambulance:

                # ambulance logout?
                if last_ambulance is not None:

                    # log ambulance logout operation
                    log.append({'client': self, 'user': self.user, 'status': ClientStatus.O.name,
                                'activity': ClientActivity.AO.name,
                                'details': last_ambulance.identifier})

                    # publish ambulance
                    publish_ambulance.add(last_ambulance)

                # ambulance login?
                if self.ambulance is not None:

                    # log ambulance login operation
                    log.append({'client': self, 'user': self.user, 'status': ClientStatus.O.name,
                                'activity': ClientActivity.AI.name,
                                'details': self.ambulance.identifier})

                    # publish ambulance
                    publish_ambulance.add(self.ambulance)

            # last hospital
            if loaded_values and self._loaded_values['hospital_id'] is not None:
                last_hospital = Hospital.objects.get(id=self._loaded_values['hospital_id'])
            else:
                last_hospital = None

            # changed hospital?
            if last_hospital != self.hospital:

                # hospital logout?
                if last_hospital is not None:

                    # log hospital logout operation
                    log.append({'client': self, 'user': self.user, 'status': ClientStatus.O.name,
                                'activity': ClientActivity.HO.name,
                                'details': last_hospital.name})

                    # publish hospital
                    publish_hospital.add(last_hospital)

                # hospital login?
                if self.hospital is not None:

                    # log hospital login operation
                    log.append({'client': self, 'user': self.user, 'status': ClientStatus.O.name,
                                'activity': ClientActivity.HI.name,
                                'details': self.hospital.name})

                    # publish hospital
                    publish_hospital.add(self.hospital)

        # offline or disconnected
        elif self.status == ClientStatus.D.name or self.status == ClientStatus.F.name:

            # has ambulance?
            if loaded_values and self._loaded_values['ambulance_id'] is not None:

                # log ambulance logout activity
                last_ambulance = Ambulance.objects.get(id=self._loaded_values['ambulance_id'])
                log.append({'client': self, 'user': self.user, 'status': self.status,
                            'activity': ClientActivity.AO.name,
                            'details': last_ambulance.identifier})

                if self.status == ClientStatus.F.name and last_ambulance.status != AmbulanceStatus.UK.name:

                    # change status of ambulance to unknown; do not publish yet
                    last_ambulance.status = AmbulanceStatus.UK.name
                    last_ambulance.save(publish=False)

                # publish ambulance
                publish_ambulance.add(last_ambulance)

            if self.ambulance is not None:

                # log warning
                logger.error("Client.save() called with status '{}' and ambulance '{} not None".format(self.status,
                                                                                                       self.ambulance))

                # logout ambulance
                self.ambulance = None

            # has hospital?
            if loaded_values and self._loaded_values['hospital_id'] is not None:

                # log hospital logout activity
                last_hospital = Hospital.objects.get(id=self._loaded_values['hospital_id'])
                log.append({'client': self, 'user': self.user, 'status': self.status,
                            'activity': ClientActivity.HO.name,
                            'details': last_hospital.name})

                # publish hospital
                publish_hospital.add(last_hospital)

            if self.hospital is not None:
                # log warning
                logger.error("Client.save() called with status '{}' and hospital '{} not None".format(self.status,
                                                                                                      self.hospital))

                # logout hospital
                self.hospital = None

            # log operation
            log.append({'client': self, 'user': self.user, 'status': self.status, 'activity': ClientActivity.HS.name})

        # check permissions
        if self.ambulance is not None or self.hospital is not None:

            permissions = get_permissions(self.user)
            if self.ambulance is not None and not permissions.check_can_write(ambulance=self.ambulance.id):
                raise PermissionDenied(_('Cannot write on ambulance'))

            if self.hospital is not None and not permissions.check_can_write(hospital=self.hospital.id):
                raise PermissionDenied(_('Cannot write on hospital'))

        # call super
        super().save(*args, **kwargs)

        # save logs
        for entry in log:
            # logger.debug(entry)
            ClientLog.objects.create(**entry)

        if env.bool("DJANGO_ENABLE_MQTT_PUBLISH", default=True):

            # publish to mqtt
            # logger.debug('publish_ambulance = {}'.format(publish_ambulance))
            # logger.debug('publish_hospital = {}'.format(publish_hospital))
            from mqtt.publish import SingletonPublishClient

            for ambulance in publish_ambulance:
                SingletonPublishClient().publish_ambulance(ambulance)

            for hospital in publish_hospital:
                SingletonPublishClient().publish_hospital(hospital)


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

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name=_('user'))

    status = models.CharField(_('status'), max_length=1,
                              choices=make_choices(ClientStatus))

    activity = models.CharField(_('activity'), max_length=2,
                                choices=make_choices(ClientActivity))

    details = models.CharField(_('details'), max_length=100, blank=True)

    updated_on = models.DateTimeField(_('updated_on'), auto_now=True)
