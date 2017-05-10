from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
import datetime
from django.utils import timezone

from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point

Tijuana = Point(-117.0382, 32.5149, srid=4326)
DefaultRoute = LineString((0, 0), (1, 1), srid=4326)

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
    id = models.AutoField(primary_key=True, default="1")
    name = models.CharField(max_length=254, default = "")
    # address-related info
    residential_unit = models.CharField(max_length=254, default = "None")
    stmain_number = models.CharField(max_length=254, default = "None")
    delegation = models.CharField(max_length=254, default = "None")
    zipcode = models.CharField(max_length=254, default = "22500")
    city = models.CharField(max_length=254, default="Tijuana")
    state = models.CharField(max_length=254, default="Baja California")
    location = models.PointField(srid=4326, default=Tijuana)
    # assignment = base name and #
    assignment = models.CharField(max_length=254, default = "None")
    # short description of the patient's injury
    description = models.CharField(max_length=500, default = "None")
    # ambulance assigned to Call
    ambulance = models.CharField(max_length=254, default = "None")
    # response time related info
    call_time = models.DateTimeField(default = timezone.now)
    departure_time = models.DateTimeField(blank = True, null = True)
    transfer_time = models.DateTimeField(blank = True, null = True)
    hospital_time = models.DateTimeField(blank = True, null = True)
    base_time = models.DateTimeField(blank = True, null = True)



    PRIORITIES = [('A','A'),('B','B'),('C','C'),('D','D'),('E','E')]
    priority = models.CharField(max_length=254, choices=PRIORITIES, default='A')

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

    id = models.AutoField(primary_key=True)
    hospital = models.ForeignKey(Hospital, related_name='equipment',on_delete=models.CASCADE, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.IntegerField()


class Base(models.Model):
    name = models.CharField(max_length=254, unique=True)
    location = models.PointField(srid=4326, null=True)


class Route(models.Model):
    name = models.CharField(max_length=50, null=False, default="Default Route Name")
    path = models.LineStringField(srid=4326, null=False, default=DefaultRoute)
    # Think about abstraction?
    type = models.CharField(max_length=50, null=False, default="Default Type")


class LocationPoint(models.Model):
    location = models.PointField(srid=4326, default=Tijuana)
    ambulance = models.ForeignKey(Ambulances, on_delete=models.CASCADE, default=1)
    timestamp = models.DateTimeField()
