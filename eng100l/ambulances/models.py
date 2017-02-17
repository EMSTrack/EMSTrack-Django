from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse

#from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

Tijuana = Point(-117.0382, 32.5149, srid=4326)

# Create your models here.

class Reporter(models.Model):
        user         = models.ForeignKey(User, on_delete=models.CASCADE)
	badge_number = models.CharField(max_length=254)

	def __str__(self):
		return "{} {}, {}".format(self.user.first_name,
                                          self.user.last_name,
                                          self.badge_number)

class Ambulances(models.Model):
	license_plate = models.CharField(max_length=254, primary_key=True)
	status	      = models.CharField(max_length=254, default="Idle")
	location      = models.PointField(srid=4326, default=Tijuana)
	reporter      = models.OneToOneField(Reporter, blank=True, null=True)

	def __str__(self):
	        return "{}: ({}), {}".format(self.license_plate,
                                             self.status,
                                             self.location)
