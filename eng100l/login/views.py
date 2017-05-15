from django.http.response import HttpResponse, HttpResponseForbidden
from django.contrib.auth import views as auth_views
from django.views.generic.edit import FormView

from braces.views import CsrfExemptMixin

from login.forms import AuthenticationForm

class MQTTLoginView(CsrfExemptMixin, FormView):
    template_name = 'login/mqtt_login.html'
    form_class = AuthenticationForm
    
    def form_invalid(self, form):
        return HttpResponseForbidden()
    
    def form_valid(self, form):
        return HttpResponse('OK')
    
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

