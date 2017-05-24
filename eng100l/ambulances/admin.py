from django.contrib import admin

# Register your models here.

from .models import Ambulances, Status, Call, Region, Hospital, Equipment, EquipmentCount, Capability, LocationPoint

admin.site.register(Ambulances)
admin.site.register(Status)
admin.site.register(Region)
admin.site.register(Call)
admin.site.register(Hospital)
admin.site.register(Equipment)
admin.site.register(EquipmentCount)
admin.site.register(Capability)
admin.site.register(LocationPoint)
