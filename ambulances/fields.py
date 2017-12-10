from .models import Status, Capability

from rest_framework import serializers

# Defines custom fields for Django REST Serializers

# To translate between status id and status name in the returned JSON
class StatusField(serializers.Field):

    def to_representation(self, obj):
        return Status.objects.filter(id=obj.id).first().name

    def to_internal_value(self, data):
        return Status.objects.filter(name=data).first()

# To translate between capability id and capability name in the returned JSON
class CapabilityField(serializers.Field):

    def to_representation(self, obj):
        return Capability.objects.filter(id=obj.id).first().name

    def to_internal_value(self, data):
        return Capability.objects.filter(name=data).first()
    
