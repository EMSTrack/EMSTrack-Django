from django.contrib import admin

from .models import Hospital
from equipment.models import Equipment, EquipmentItem

from emstrack.admin import EMSTrackAdmin


# Register classes

admin.site.register(Hospital, EMSTrackAdmin)
admin.site.register(Equipment, EMSTrackAdmin)
admin.site.register(EquipmentItem, EMSTrackAdmin)
