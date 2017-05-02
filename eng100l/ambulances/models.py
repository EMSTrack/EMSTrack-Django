from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse

from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

Tijuana = Point(-117.0382, 32.5149, srid=4326)

# Create your models here.

class Status(models.Model):
    name = models.CharField(max_length=254, unique=True)

    def __str__(self):
        return "{}".format(self.name)

class TrackableDevice(models.Model):
    device_id = models.CharField(max_length=254, primary_key=True)
    location = models.PointField(srid=4326, default=Tijuana)

class Ambulances(models.Model):
    license_plate = models.CharField(max_length=254, primary_key=True)
    name = models.CharField(max_length=254, default = "1")
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
    call_time = models.DateTimeField(default=timezone.now )
    assignment = models.CharField(max_length=254, default = "none")
    state = models.CharField(max_length=254)
    st_main = models.CharField(max_length=254)
    colony = models.CharField(max_length=254, default="A")
    delegation = models.CharField(max_length=254)
    ambulance_no = models.PositiveSmallIntegerField(default=0)


class Region(models.Model):
    name = models.CharField(max_length=254, unique=True)
    center = models.PointField(srid=4326, null=True)

class Hospital(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254, default="")
    address = models.CharField(max_length=254, default="")

    def __str__(self):
        return "{}".format(self.name)

class Equipment(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254)

    def __str__(self):
        return "{}".format(self.name)


class EquipmentCount(models.Model):
    id = models.AutoField(primary_key=True)
    hospital = models.ForeignKey(Hospital, related_name='equipment',
        on_delete=models.CASCADE, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.IntegerField()
