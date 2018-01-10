from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Register your models here.

from .models import Hospital, Equipment, HospitalEquipment

admin.site.register(Hospital)
admin.site.register(Equipment)
admin.site.register(HospitalEquipment)
