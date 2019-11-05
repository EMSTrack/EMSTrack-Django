from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from import_export import resources, fields


class UserResource(resources.ModelResource):
    is_dispatcher = fields.Field(attribute='userprofile__is_dispatcher')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_dispatcher', 'is_active')
