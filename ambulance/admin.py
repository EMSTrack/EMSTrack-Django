from django.contrib import admin
from django.contrib.gis.db import models

from emstrack.forms import LeafletPointWidget

from .models import Ambulance, AmbulanceUpdate, \
    AmbulanceCallTime, Patient, Call, \
    Location, \
    Region

# Override location widget in the admin
class AmbulanceAdmin(admin.ModelAdmin):

    formfield_overrides = {
        models.PointField: {'widget': LeafletPointWidget(attrs={'map_width': 500,'map_height': 300})},
    }

# Register classes
admin.site.register(Ambulance, AmbulanceAdmin)
admin.site.register(AmbulanceUpdate, AmbulanceAdmin)

admin.site.register(AmbulanceCallTime, AmbulanceAdmin)
admin.site.register(Patient, AmbulanceAdmin)
admin.site.register(Call, AmbulanceAdmin)

admin.site.register(Location, AmbulanceAdmin)

admin.site.register(Region, AmbulanceAdmin)
