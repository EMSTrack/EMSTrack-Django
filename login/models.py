from django.contrib.gis.db import models

from django.contrib.auth.models import User

from ambulance.models import Ambulance

from hospital.models import Hospital


# Ambulance and Hospital Permissions

class AmbulancePermission(models.Model):

    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)

    def __str__(self):
        return '{}(id={}): read[{}] write[{}]'.format(self.ambulance.identifier,
                                                      self.ambulance.id,
                                                      self.can_read,
                                                      self.can_write)


class HospitalPermission(models.Model):

    hospital = models.ForeignKey(Hospital,
                                  on_delete=models.CASCADE)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)

    def __str__(self):
        return '{}(id={}): read[{}] write[{}]'.format(self.hospital.name,
                                                      self.hospital.id,
                                                      self.can_read,
                                                      self.can_write)


# Profile

class Profile(models.Model):

    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)
    ambulances = models.ManyToManyField(AmbulancePermission)
    hospitals = models.ManyToManyField(HospitalPermission)

    def __str__(self):
        return ('Ambulances:\n' +
                '\n'.join('  {}'.format(k) for k in self.ambulances.all()) +
                '\nHospitals:\n' +
                '\n'.join('  {}'.format(k) for k in self.hospitals.all()))
    

# TemporaryPassword

class TemporaryPassword(models.Model):

    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)
    password = models.CharField(max_length=254)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '"{}" (created on: {})'.format(self.password, self.created_on)