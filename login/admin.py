from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

# Register your models here.

from .models import UserProfile, GroupProfile, \
    UserAmbulancePermission, UserHospitalPermission, \
    GroupAmbulancePermission, GroupHospitalPermission


# Define an inline admin descriptor for Profile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class GroupProfileInline(admin.StackedInline):
    model = GroupProfile
    can_delete = False


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Define a new Group admin
class GroupAdmin(BaseGroupAdmin):
    inlines = (GroupProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Re-register GroupAdmin
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

# Register AmbulancePermission and HospitalPermission
admin.site.register(UserAmbulancePermission)
admin.site.register(UserHospitalPermission)
admin.site.register(GroupAmbulancePermission)
admin.site.register(GroupHospitalPermission)
