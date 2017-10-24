from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

# Register your models here.

from .models import Ambulances, Status, Call, Region, \
    Hospital, Equipment, EquipmentCount, Capability, LocationPoint, \
    User 

# creates the form with new fields using the UserModel
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

# adds the new fields to the form
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('hospitals', 'hospital', 'ambulances', 'ambulance',)}),)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Ambulances)
admin.site.register(Status)
admin.site.register(Region)
admin.site.register(Call)
admin.site.register(Hospital)
admin.site.register(Equipment)
admin.site.register(EquipmentCount)
admin.site.register(Capability)
admin.site.register(LocationPoint)
