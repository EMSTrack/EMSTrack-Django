from django.contrib import admin
from django.contrib.gis.db import models

from emstrack.forms import LeafletPointWidget


# Override location widget in the admin
class EMSTrackAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {'widget': LeafletPointWidget(attrs={'map_width': 500, 'map_height': 300})},
    }
