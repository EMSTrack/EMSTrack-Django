from django.utils import timezone

from django.db import models

from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point

Tijuana = Point(-117.0382, 32.5149, srid=4326)
DefaultRoute = LineString((0, 0), (1, 1), srid=4326)

from django.contrib.auth.models import User

# User and ambulance location models

class UserLocation(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    location = models.PointField(srid=4326)
    timestamp = models.DateTimeField()

    def __str__(self):
        return "{}".format(self.location)

class AmbulanceLocation(models.Model):
    location = models.ForeignKey(UserLocation, on_delete=models.CASCADE)
    
    AMBULANCE_STATUS_CHOICES = [
        ('AV','Available'),
        ('OS','Out of service'),
        ('PB','Patient bound'),
        ('AP','At patient'),
        ('HB','Hospital bound'),
        ('AH','At hospital'),
    ]
    status = models.CharField(max_length=2,
                              choices=AMBULANCE_STATUS_CHOICES)
    
    orientation = models.FloatField(default=0.0)

    def __str__(self):
        return "{}".format(self.location)

# Ambulance model
    
class Ambulance(models.Model):
    identifier = models.CharField(max_length=50, unique=True)
    comment = models.CharField(max_length=254, default="")

    AMBULANCE_CAPABILITY_CHOICES = [
        ('B','Basic'),
        ('A','Advanced'),
        ('R','Rescue')
    ]
    capability = models.CharField(max_length=1,
                                  choices = AMBULANCE_CAPABILITIES_CHOICES)
    
    updated_at = models.DateTimeField(auto_now=True)
    location =  models.ForeignKey(AmbulanceLocation,
                                  on_delete=models.CASCADE,
                                  null=True)
    
    def __str__(self):
        return self.identifier

class AmbulanceRoute(models.Model):
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    points = models.ManyToManyField(AmbulanceLocation)
    
class AmbulancePermission(models.Model):
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    
# Hospital model

class Hospital(models.Model):
    name = models.CharField(max_length=254, default="")
    address = models.CharField(max_length=254, default="")
    location = models.PointField(srid=4326, null=True, blank=True)
    
    def __str__(self):
        return "{}: {} ({})".format(self.id, self.name, self.address)

class HospitalPermission(models.Model):
    hospital = models.ForeignKey(Hospital,
                                  on_delete=models.CASCADE)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)

# Profile and state

class Profile(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)
    ambulances = models.ManyToManyField(AmbulancePermission)
    hospitals = models.ManyToManyField(HospitalPermission)

class State(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.CASCADE,
                                 null=True, blank=True)
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE,
                                  null=True, blank=True)

# THESE NEED REVISING
    
class Call(models.Model):
    #call metadata (status not required for now)
    active = models.BooleanField(default=False)
    status = models.CharField(max_length=254, default= "", blank=True)
    # ambulance assigned to Call (Foreign Key)
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE, default=1)
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
    # response time related info
    call_time = models.DateTimeField(default = timezone.now)
    departure_time = models.DateTimeField(blank = True, null = True)
    transfer_time = models.DateTimeField(blank = True, null = True)
    hospital_time = models.DateTimeField(blank = True, null = True)
    base_time = models.DateTimeField(blank = True, null = True)
    PRIORITIES = [('A','A'),('B','B'),('C','C'),('D','D'),('E','E')]
    priority = models.CharField(max_length=254, choices=PRIORITIES, default='A')

    def __str__(self):
        return "({}): {}, {}".format(self.priority, self.residential_unit, self.stmain_number)


class Region(models.Model):
    name = models.CharField(max_length=254, unique=True)
    center = models.PointField(srid=4326, null=True)

    def __str__(self):
        return self.name

class Equipment(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254)
    toggleable = models.BooleanField(default=0)

    def __str__(self):
        return "{}: {} ({})".format(self.id, self.name, self.toggleable)

class EquipmentCount(models.Model):
    id = models.AutoField(primary_key=True)
    hospital = models.ForeignKey(Hospital, related_name='equipment',on_delete=models.CASCADE, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('hospital', 'equipment',)

    def __str__(self):
        return "Hospital: {}, Equipment: {}, Count: {}".format(self.hospital, self.equipment, self.quantity)


class Base(models.Model):
    name = models.CharField(max_length=254, unique=True)
    location = models.PointField(srid=4326, null=True)

    def __str__(self):
        return self.name



