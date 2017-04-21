from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse

from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

Tijuana = Point(-117.0382, 32.5149, srid=4326)

# Create your models here.

class Status(models.Model):
    status_string = models.CharField(max_length=254, primary_key=True)

    def __str__(self):
        return "{}".format(self.status_string)

class TrackableDevice(models.Model):
    device_id = models.CharField(max_length=254, primary_key=True)
    location = models.PointField(srid=4326, default=Tijuana)

class Ambulances(models.Model):
    license_plate = models.CharField(max_length=254, primary_key=True)
    status        = models.CharField(max_length=254, default="Idle")
    location      = models.PointField(srid=4326, default=Tijuana)
    device        = models.OneToOneField(TrackableDevice, blank=True, null=True)

    def __str__(self):
        return "{}: ({}), {}".format(self.license_plate,
                                     self.status,
                                     self.location)

class Call(models.Model):
    address_string = models.CharField(max_length=254, primary_key=True)
    location = models.PointField(srid=4326, default=Tijuana)
    priority = models.CharField(max_length=254, default="A")


    def __str__(self):
        return "{}: ({}), {}".format(self.address_string,self.location,self.priority)    
