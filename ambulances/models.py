from django.utils import timezone

from django.db import models
from django.conf import settings

from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point
from django.contrib.auth.models import AbstractUser

from django.db.models.signals import post_save
from django.dispatch import receiver

Tijuana = Point(-117.0382, 32.5149, srid=4326)
DefaultRoute = LineString((0, 0), (1, 1), srid=4326)

# Model schemas for the database

class User(AbstractUser):
    pass

class AmbulanceStatus(models.Model):
    name = models.CharField(max_length=254, unique=True)

    def __str__(self):
        return "{}".format(self.name)

class AmbulanceCapability(models.Model):
    name = models.CharField(max_length=254, unique=True)

    def __str__(self):
        return "{}".format(self.name)

class UserLocation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    location = models.PointField(srid=4326)
    timestamp = models.DateTimeField()

    def __str__(self):
        return "{}".format(self.location)

class AmbulanceLocation(models.Model):
    location = models.ForeignKey(UserLocation, on_delete=models.CASCADE)
    status = models.ForeignKey(AmbulanceStatus, on_delete=models.CASCADE)
    orientation = models.FloatField(default=0.0)

    def __str__(self):
        return "{}".format(self.location)
    
class Ambulance(models.Model):
    identifier = models.CharField(max_length=50, unique=True)
    comment = models.CharField(max_length=254, default="")
    capability = models.ForeignKey(AmbulanceCapability,
                                   on_delete=models.CASCADE,
                                   null=True, blank=True)
    
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
    
class Hospital(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254, default="")
    address = models.CharField(max_length=254, default="")

    def __str__(self):
        return "{}: {} ({})".format(self.id, self.name, self.address)

class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.CASCADE,
                                 null=True, blank=True, 
                                 related_name="hosp_id")
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE,
                                  null=True, blank=True,
                                  related_name ="ambul_id")
    
    hospitals = models.ManyToManyField(Hospital)
    ambulances = models.ManyToManyField(Ambulance)
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    
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



