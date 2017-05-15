import django.contrib.auth.forms as auth_forms
import django.forms as forms
from django.utils.translation import ugettext_lazy as _

class AuthenticationForm(auth_forms.AuthenticationForm):
    username = auth_forms.UsernameField(
        max_length=254,
        widget=forms.TextInput(
            attrs={'autofocus': True,
                   'placeholder': 'Email',
                   'class': 'form-control input-lg',
                   'style': 'margin-bottom: 30px;',
                   'required': True}
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Password',
                   'class': 'form-control input-lg',
                   'required': True}
        ),
    )
