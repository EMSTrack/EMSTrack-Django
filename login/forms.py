from datetime import timedelta

import django.forms as forms
import django.contrib.auth.forms as auth_forms

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.hashers import get_hasher, check_password

from django.contrib.auth.models import User, Group
from extra_views import InlineFormSetView

from ambulance.models import Ambulance
from hospital.models import Hospital
from .models import TemporaryPassword, AmbulancePermission, HospitalPermission, GroupProfile


class SignupForm(auth_forms.UserCreationForm):
    username = auth_forms.UsernameField(
        label=_("Username"),
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={'autofocus': True,
                   'placeholder': 'Username',
                   'class': 'form-control input-lg'}
        ),
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        required=True,
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Password',
                   'class': 'form-control input-lg'}
        ),
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        strip=False,
        required=True,
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Confirm password',
                   'class': 'form-control input-lg'}
        ),
    )
    first_name = forms.CharField(
        label=_("First name"),
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'First name',
                   'class': 'form-control input-lg'}
        )
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Last name',
                   'class': 'form-control input-lg'}
        )
    )
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(
            attrs={'placeholder': 'Email',
                   'class': 'form-control input-lg'}
        )
    )
    position = forms.ModelMultipleChoiceField(
        label=_("Choose one or more groups"),
        queryset=Group.objects.all().order_by('name'),
        widget=forms.Select(
            attrs={'class': 'form-control selectpicker',
                   'multiple': True}
        )
    )

    class Meta:
        model = User
        fields = ('username',
                  'first_name', 'last_name',
                  'email',
                  'password1', 'password2', 'position' )


class AuthenticationForm(auth_forms.AuthenticationForm):
    username = auth_forms.UsernameField(
        label=_("Username"),
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={'autofocus': True,
                   'placeholder': 'Username',
                   'class': 'form-control input-lg',
                   'style': 'margin-bottom: 30px;'}
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        required=True,
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Password',
                   'class': 'form-control input-lg'}
        ),
    )
    

class MQTTAuthenticationForm(AuthenticationForm):

    """
    This form will allow authentication against a temporary password.
    The password must be retrieved using a valid session only.
    """
    
    def clean(self):

        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        # see if password is encoded as a hash
        if password: 

            # a hash is in the format: <algorithm>$<iterations>$<hash>
            parts = password.split('$')
            
            if len(parts) >= 3 and len(password) <= 128:
            
                # most likely a hash
                hasher = get_hasher()
            
                if parts[0] == hasher.algorithm:

                    # it is a hash, authenticate
                    encoded = password
                
                    try:
                    
                        # retrieve current password
                        pwd = TemporaryPassword.objects.get(user__username = username)
                        password = pwd.password
                        valid_until = pwd.created_on + timedelta(seconds=120)
                    
                        # invalidate login if password is expired
                        if timezone.now() > valid_until:
                            password = None
                    
                    except ObjectDoesNotExist:

                        password = None

                    # check password
                    if password is not None and check_password(password, encoded):

                        # confirm user login allowed
                        self.confirm_login_allowed(pwd.user)
                    
                        # valid login
                        return self.cleaned_data
                
                    # otherwise it is an invalid login
                    raise forms.ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                        params={'username': self.username_field.verbose_name},
                    )
            
        # if not a hash, call super to validate password
        return super().clean()


class UserAdminCreateForm(forms.ModelForm):

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']


class UserAdminUpdateForm(UserAdminCreateForm):

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

        # disable username
        self.fields['username'].disabled = True


class AmbulancePermissionModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.identifier


class HospitalPermissionModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class AmbulancePermissionAdminForm(forms.ModelForm):
    ambulance = AmbulancePermissionModelChoiceField(queryset=Ambulance.objects.all())

    class Meta:
        model = AmbulancePermission
        fields = ['ambulance', 'can_read', 'can_write']


class HospitalPermissionAdminForm(forms.ModelForm):
    hospital = HospitalPermissionModelChoiceField(queryset=Hospital.objects.all())

    class Meta:
        model = HospitalPermission
        fields = ['hospital', 'can_read', 'can_write']


class GroupProfileAdminForm(forms.ModelForm):

    class Meta:
        model = GroupProfile
        fields = ['description']


class GroupAdminCreateForm(forms.ModelForm):

    name = forms.CharField()

    class Meta:
        model = GroupProfile
        fields = ['description']


class GroupAdminUpdateForm(GroupAdminCreateForm):

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

        # disable name
        self.fields['name'].disabled = True
