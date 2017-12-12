from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.

from .models import User, \
    Ambulance, AmbulanceStatus, AmbulanceCapability, \
    AmbulanceLocation, \
    User, UserLocation, \
    Hospital, Equipment, EquipmentCount, UserLocation, \
    Call, Region

admin.site.register(User, UserAdmin)

admin.site.register(Ambulance)
admin.site.register(AmbulanceStatus)
admin.site.register(AmbulanceCapability)
admin.site.register(AmbulanceLocation)
admin.site.register(Region)
admin.site.register(Call)
admin.site.register(Hospital)
admin.site.register(Equipment)
admin.site.register(EquipmentCount)
admin.site.register(UserLocation)
