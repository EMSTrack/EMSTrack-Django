from django.http.response import HttpResponse, HttpResponseForbidden
from django.contrib.auth import views as auth_views
from django.views.generic.base import View
from django.views.generic.edit import FormView

#from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()

from braces.views import CsrfExemptMixin

from login.forms import AuthenticationForm, SignupForm

# signup
class SignupView(FormView):
    template_name = 'login/signup.html'
    form_class = SignupForm

# # login
class LoginView(auth_views.LoginView):
     template_name = 'login/login.html'
     authentication_form = AuthenticationForm

# # logout
class LogoutView(auth_views.LogoutView):
     next_page = '/ambulances'

# MQTT login views

class MQTTLoginView(CsrfExemptMixin, FormView):
    template_name = 'login/mqtt_login.html'
    form_class = AuthenticationForm
    
    def form_invalid(self, form):
        return HttpResponseForbidden()
    
    def form_valid(self, form):
        return HttpResponse('OK')
    
class MQTTSuperuserView(CsrfExemptMixin, View):
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        data = {}
        if hasattr(request, 'POST'):  # pragma: no cover
            data = request.POST
        elif hasattr(request, 'DATA'):  # pragma: no cover
            data = request.DATA
        try:
            if User.objects.get(username=data.get('username'),
                                is_active=True).is_superuser:
                return HttpResponse('OK')
            
        except User.DoesNotExist:
            pass
        
        return HttpResponseForbidden()

class MQTTAclView(CsrfExemptMixin, View):
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        data = {}
        if hasattr(request, 'POST'):  # pragma: no cover
            data = request.POST
        elif hasattr(request, 'DATA'):  # pragma: no cover
            data = request.DATA
        allow = False

        # Check permissions
        username = data.get('username')
        acc = data.get('acc') # 1 == sub, 2 == pub

        # get topic and remove first '/'
        topic = data.get('topic').split('/')
        if len(topic) > 0 and topic[0] == '':
            del topic[0]

        try:
            # get user
            user = User.objects.get(username=data.get('username'),
                                    is_active=True)

            if acc == '1':
                
                # permission to subscribe
                #  - all (for now)
                
                return HttpResponse('OK')
            
            elif acc == '2':
                
                # permission to publish on:
                #  - user/*username*/hospital
                #  - user/*username*/ambulance
                #  - user/*username*/location
                if (len(topic) >= 3 and
                    topic[0] == 'user' and
                    topic[1] == user.username):

                    if (topic[2] == 'hospital' or
                        topic[2] == 'ambulance' or
                        topic[2] == 'location'):
                        
                        return HttpResponse('OK')
        
        except User.DoesNotExist:
            pass
        
        return HttpResponseForbidden()
