from .models import Status

from rest_framework import serializers


# To translate between status id and status name in the returned JSON
class StatusField(serializers.Field):

    def to_representation(self, obj):
        return Status.objects.filter(id=obj.id).first().name

    def to_internal_value(self, data):
        return Status.objects.filter(name=data).first()
