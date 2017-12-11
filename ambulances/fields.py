from .models import AmbulanceStatus, AmbulanceCapability

from rest_framework import serializers

# Defines custom fields for Django REST Serializers

# To translate between status id and status name in the returned JSON
class AmbulanceStatusField(serializers.Field):

    def to_representation(self, obj):
        return AmbulanceStatus.objects.filter(id=obj.id).first().name

    def to_internal_value(self, data):
        return AmbulanceStatus.objects.filter(name=data).first()

# To translate between capability id and capability name in the returned JSON
class CapabilityField(serializers.Field):

    def to_representation(self, obj):
        return AmbulanceCapability.objects.filter(id=obj.id).first().name

    def to_internal_value(self, data):
        return AmbulanceCapability.objects.filter(name=data).first()
    
