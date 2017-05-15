from django.contrib.auth import views as auth_views
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from login.forms import AuthenticationForm

@method_decorator(csrf_exempt, name='dispatch')
class MQTTLoginView(auth_views.LoginView):
    template_name = 'login/login.html'
    authentication_form = AuthenticationForm
    
class LoginView(auth_views.LoginView):
    template_name = 'login/login.html'
    authentication_form = AuthenticationForm

class LogoutView(auth_views.LogoutView):
    next_page = '/ambulances'

class PasswordChangeView(auth_views.PasswordChangeView):
    pass

class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    pass

class PasswordResetView(auth_views.PasswordResetView):
    pass

class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    pass

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    pass

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    pass

