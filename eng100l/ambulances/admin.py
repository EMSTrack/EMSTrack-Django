from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.

from .models import Ambulances, Status, Call, Region, \
    Hospital, Equipment, EquipmentCount, Capability, LocationPoint, \
    User 

admin.site.register(User, UserAdmin)
admin.site.register(Ambulances)
admin.site.register(Status)
admin.site.register(Region)
admin.site.register(Call)
admin.site.register(Hospital)
admin.site.register(Equipment)
admin.site.register(EquipmentCount)
admin.site.register(Capability)
admin.site.register(LocationPoint)
