from django.contrib.gis.db import models

from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.validators import MinValueValidator
from django.urls import reverse

from ambulance.models import Ambulance

from hospital.models import Hospital


# Profile

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
        ordering = ['priority']


# Group Ambulance and Hospital Permissions

class Permission(models.Model):
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)

    class Meta:
        abstract = True


class UserAmbulancePermission(Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'ambulance')

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.user,
                                                         self.ambulance.identifier,
                                                         self.ambulance.id,
                                                         self.can_read,
                                                         self.can_write)


class UserHospitalPermission(Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'hospital')

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.user,
                                                         self.hospital.name,
                                                         self.hospital.id,
                                                         self.can_read,
                                                         self.can_write)


class GroupAmbulancePermission(Permission):
    group = models.ForeignKey(Group,
                              on_delete=models.CASCADE)
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE)

    class Meta:
        unique_together = ('group', 'ambulance')

    def __str__(self):
        return '{}/{}(id={}): read[{}] write[{}]'.format(self.group,
                                                         self.ambulance.identifier,
                                                         self.ambulance.id,
                                                         self.can_read,
                                                         self.can_write)


class GroupHospitalPermission(Permission):
    group = models.ForeignKey(Group,
                              on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.CASCADE)

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
                                on_delete=models.CASCADE)
    password = models.CharField(max_length=254)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '"{}" (created on: {})'.format(self.password, self.created_on)
