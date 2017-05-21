from django.http.response import HttpResponse, HttpResponseForbidden
from django.contrib.auth import views as auth_views
from django.views.generic.base import View
from django.views.generic.edit import FormView
from django.contrib.auth.models import User

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

        # TO DO
        return HttpResponse('OK')
        
        # if hasattr(settings, 'MQTT_ACL_ALLOW'):
        #     allow = settings.MQTT_ACL_ALLOW

        # topic, new_topic = Topic.objects.get_or_create(name=data.get('topic', '#'))
        # acc = data.get('acc', None)
        # user = None
        # user_ = User.objects.filter(username=data.get('username'), is_active=True)
        # if user_.count() > 0:
        #     user = user_[0]

        # acl = None
        # if not new_topic:
        #     try:
        #         acl = ACL.objects.get(acc=acc, topic=topic)  # ACL only count have one or none
        #     except ACL.DoesNotExist:
        #         pass

        # if acl is None:
        #     allow = ACL.get_default(acc=acc, user=user)
        #     # TODO search best candidate

        # if acl:
        #     allow = acl.has_permission(user=user)

        # if allow and hasattr(settings, 'MQTT_ACL_ALLOW_ANONIMOUS'):
        #     if user is None:
        #         allow = settings.MQTT_ACL_ALLOW_ANONIMOUS

        # if not allow:
        #     return HttpResponseForbidden('')
        # return HttpResponse('')
