from django.contrib import admin

# Register your models here.

from .models import TrackableDevice, Ambulances, Status, Call, Region, Hospital, Equipment, EquipmentCount

admin.site.register(TrackableDevice)
admin.site.register(Ambulances)
admin.site.register(Status)
admin.site.register(Region)
admin.site.register(Call)
admin.site.register(Hospital)
admin.site.register(Equipment)
admin.site.register(EquipmentCount)
