from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.

from .models import Profile, \
    Ambulance, AmbulanceStatus, AmbulanceCapability, \
    AmbulanceLocation, \
    User, UserLocation, \
    Hospital, Equipment, EquipmentCount, UserLocation, \
    Call, Region

# Define an inline admin descriptor for Profile model
# which acts a bit like a singleton
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, )

# Re-register UserAdmin
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
