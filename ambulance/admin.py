from django.contrib import admin
from django.contrib.gis.db import models

from .models import Ambulance, AmbulanceUpdate, \
    AmbulanceCall, Patient, Call, \
    Location, \
    Region

from emstrack.admin import EMSTrackAdmin

# Register classes
admin.site.register(Ambulance, EMSTrackAdmin)
admin.site.register(AmbulanceUpdate, EMSTrackAdmin)

admin.site.register(AmbulanceCall, EMSTrackAdmin)
admin.site.register(Patient, EMSTrackAdmin)
admin.site.register(Call, EMSTrackAdmin)

admin.site.register(Location, EMSTrackAdmin)

admin.site.register(Region, EMSTrackAdmin)
