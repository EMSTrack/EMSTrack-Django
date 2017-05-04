from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse

from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

Tijuana = Point(-117.0382, 32.5149, srid=4326)

# Create your models here.

class Status(models.Model):
    name = models.CharField(max_length=254, unique=True, default="")

    def __str__(self):
        return "{}".format(self.name)

class TrackableDevice(models.Model):
    device_id = models.CharField(max_length=254, primary_key=True)
    location = models.PointField(srid=4326, default=Tijuana)

class Ambulances(models.Model):
    license_plate = models.CharField(max_length=254, primary_key=True)
    name = models.CharField(max_length=254, default="")
    status = models.ForeignKey(Status, on_delete=models.CASCADE, default=1)
    location      = models.PointField(srid=4326, default=Tijuana)
    # device        = models.OneToOneField(TrackableDevice, blank=True, null=True)
    priority = models.CharField(max_length=254, default="High")

    def __str__(self):
        return "{}: ({}), {}".format(self.license_plate,
                                     self.status,
                                     self.location)

class Call(models.Model):
    address = models.CharField(max_length=254, primary_key=True)
    location = models.PointField(srid=4326, default=Tijuana)
    priority = models.CharField(max_length=254, default="A")

class Region(models.Model):
    name = models.CharField(max_length=254, unique=True)
    center = models.PointField(srid=4326, null=True)

class Hospital(models.Model):
    name = models.CharField(max_length=254, default="")
    address = models.CharField(max_length=254, default="")

    def __str__(self):
        return "{}".format(self.name)

class Equipment(models.Model):

    name = models.CharField(max_length=254)
    equipment_type = models.CharField(max_length=254)
    toggleable = models.BooleanField(default=0)

    def __str__(self):
        return "{}".format(self.name)


class EquipmentCount(models.Model):
    hospital = models.ForeignKey(Hospital, related_name='equipment', 
        on_delete=models.CASCADE, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.IntegerField()
