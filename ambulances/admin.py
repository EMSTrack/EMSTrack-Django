from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Register your models here.

from .models import Ambulance, \
    Hospital, Equipment, HospitalEquipment, \
    Call, Region

admin.site.register(Ambulance)

admin.site.register(Hospital)
admin.site.register(Equipment)
admin.site.register(HospitalEquipment)

admin.site.register(Region)
admin.site.register(Call)
