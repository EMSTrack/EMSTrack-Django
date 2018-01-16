from rest_framework import serializers

class LocationSerializer(serializers.Serializer):

    # Define functions that will query for these custom fields
    latitude = serializers.SerializerMethodField('get_lat')
    longitude = serializers.SerializerMethodField('get_long')

    class Meta:
        model = LocationPoint
        fields = ['latitude', 'longitude']

    def get_lat(self, obj):
        return obj.location.y

    def get_long(self, obj):
        return obj.location.x
