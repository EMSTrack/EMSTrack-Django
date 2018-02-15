from django.contrib import admin

# Register your models here.

from .models import Ambulance, AmbulanceUpdate, \
    AmbulanceCallTimes, Patient, Call, \
    Location, \
    Region

admin.site.register(Ambulance)
admin.site.register(AmbulanceUpdate)

admin.site.register(AmbulanceCallTimes)
admin.site.register(Patient)
admin.site.register(Call)

admin.site.register(Location)

admin.site.register(Region)
