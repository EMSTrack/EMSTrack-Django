from django.contrib import admin

# Register your models here.

from .models import TrackableDevice, Ambulances, Status

admin.site.register(TrackableDevice)
admin.site.register(Ambulances)
admin.site.register(Status)
