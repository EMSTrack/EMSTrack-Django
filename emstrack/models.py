from django.contrib.auth.models import User

from django.contrib.gis.db import models

class AddressModel(models.Model):
    """
    An abstract base class model that provides address fields.
    """

    street = models.CharField(max_length=254, default = "")
    unit = models.CharField(max_length=30, default = "")
    number = models.CharField(max_length=30, default = "", blank = True)
    city = models.CharField(max_length=100, default = "")
    state = models.CharField(max_length=2, default = "")
    zipcode = models.CharField(max_length=12, default = "")
    country = models.CharField(max_length=2, default = "")

    location = models.PointField(srid=4326, null=True, blank=True)
    
    class Meta:
        abstract = True

class UpdatedByModel(models.Model):

    comment = models.CharField(max_length=254, default="")
    updated_by = models.ForeignKey(User,
                                   on_delete=models.CASCADE)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
