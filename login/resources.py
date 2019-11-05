from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from import_export import resources


class UserResource(resources.ModelResource):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'is_staff', 'userprofile__is_dispatcher', 'is_active')
