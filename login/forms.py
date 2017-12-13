import django.contrib.auth.forms as auth_forms
import django.forms as forms
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
#from django.contrib.auth import get_user_model
#User = get_user_model()

from django.contrib.auth.models import Group

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
    
