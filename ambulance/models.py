from enum import Enum

from django.contrib.auth.models import User
from django.contrib.gis.db import models

from django.utils import timezone
from django.urls import reverse

from emstrack.models import AddressModel, UpdatedByModel, defaults

# User and ambulance location models

# Ambulance model

class AmbulanceStatus(Enum):
    UK = 'Unknown'
    AV = 'Available'
    OS = 'Out of service'
    PB = 'Patient bound'
    AP = 'At patient'
    HB = 'Hospital bound'
    AH = 'At hospital'
    
class AmbulanceCapability(Enum):
    B = 'Basic'
    A = 'Advanced'
    R = 'Rescue'
    
class Ambulance(UpdatedByModel):

    # ambulance properties
    identifier = models.CharField(max_length=50, unique=True)

    AMBULANCE_CAPABILITY_CHOICES = \
        [(m.name, m.value) for m in AmbulanceCapability]
    capability = models.CharField(max_length=1,
                                  choices = AMBULANCE_CAPABILITY_CHOICES)
    
    # status
    AMBULANCE_STATUS_CHOICES = \
        [(m.name, m.value) for m in AmbulanceStatus]
    status = models.CharField(max_length=2,
                              choices=AMBULANCE_STATUS_CHOICES,
                              default=AmbulanceStatus.UK.name)
    
    # location
    orientation = models.FloatField(default = 0)
    location = models.PointField(srid=4326, default = defaults['location'])
    location_timestamp = models.DateTimeField(null=True, blank=True)

    @classmethod
    def from_db(cls, db, field_names, values):
        # call super
        instance = super(Ambulance, cls).from_db(db, field_names, values)
        
        # store the original field values on the instance
        instance._loaded_values = dict(zip(field_names, values))

        # return instance
        return instance
    
    def save(self, *args, **kwargs):
        # save to Ambulance
        super().save(*args, **kwargs)

        # publish to mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_ambulance(self)

        # save to AmbulanceUpdate
        data = {k: getattr(self, k)
                for k in ('status', 'orientation',
                          'location', 'location_timestamp',
                          'comment', 'updated_by', 'updated_on')}
        data['ambulance'] = self;
        obj = AmbulanceUpdate(**data)
        obj.is_valid()
        obj.save()
        
    def delete(self, *args, **kwargs):
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().remove_ambulance(self)
        super().delete(*args, **kwargs) 
    
    def get_absolute_url(self):
        return reverse('ambulance:detail', kwargs={'pk': self.id})
    
    def __str__(self):
        return ('Ambulance {}(id={}) ({}) [{}]:\n' +
                '    Status: {}\n' +
                '  Location: {} @ {}\n' +
                '   Updated: {} by {}').format(self.identifier,
                                               self.id,
                                               AmbulanceCapability[self.capability].value,
                                               self.comment,
                                               AmbulanceStatus[self.status].value,
                                               self.location,
                                               self.location_timestamp,
                                               self.updated_by,
                                               self.updated_on)

class AmbulanceUpdate(models.Model):

    # ambulance id
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE)

    # ambulance status
    AMBULANCE_STATUS_CHOICES = \
        [(m.name, m.value) for m in AmbulanceStatus]
    status = models.CharField(max_length=2,
                              choices=AMBULANCE_STATUS_CHOICES,
                              default=AmbulanceStatus.UK.name)
    
    # location
    orientation = models.FloatField(default = 0)
    location = models.PointField(srid=4326, default = defaults['location'])
    location_timestamp = models.DateTimeField(null=True, blank=True)

    # updated by
    comment = models.CharField(max_length=254, null=True, blank=True)
    updated_by = models.ForeignKey(User,
                                   on_delete=models.CASCADE)
    updated_on = models.DateTimeField()
    

class AmbulanceCallTimes(models.Model):

    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE, default=1)
    
    dispatch_time = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    patient_time = models.DateTimeField(null=True, blank=True)
    hospital_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
class Patient(models.Model):
    """
    A model that provides patient fields.
    """

    name = models.CharField(max_length=254, default = "")
    age = models.IntegerField(null=True)
        
class CallPriority(Enum):
    A = 'Urgent'
    B = 'Emergency'
    C = 'C'
    D = 'D'
    E = 'Not urgent'
    
class Call(AddressModel, UpdatedByModel):

    # active status 
    active = models.BooleanField(default=False)

    # ambulances assigned to call
    ambulances = models.ManyToManyField(AmbulanceCallTimes)

    # patients
    patients = models.ManyToManyField(Patient)
    
    # details
    details = models.CharField(max_length=500, default = "")

    # call priority
    CALL_PRIORITY_CHOICES = \
        [(m.name, m.value) for m in CallPriority]
    priority = models.CharField(max_length=1,
                                choices=CALL_PRIORITY_CHOICES,
                                default=CallPriority.E.name)
    
    def __str__(self):
        return "{} ({})".format(self.location, self.priority)

    
# THOSE NEED REVIEWING
    
class Region(models.Model):
    name = models.CharField(max_length=254, unique=True)
    center = models.PointField(srid=4326, null=True)

    def __str__(self):
        return self.name


class Base(models.Model):
    name = models.CharField(max_length=254, unique=True)
    location = models.PointField(srid=4326, null=True)

    def __str__(self):
        return self.name
