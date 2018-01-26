from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse, HttpResponseForbidden
from django.contrib.auth import views as auth_views
from django.views.generic.base import View
from django.views.generic.edit import FormView

from django.contrib.auth.models import User

from braces.views import CsrfExemptMixin

from .forms import AuthenticationForm, SignupForm

from .models import TemporaryPassword

# signup
class SignupView(FormView):
    template_name = 'login/signup.html'
    form_class = SignupForm

# login
class LoginView(auth_views.LoginView):
     template_name = 'login/login.html'
     authentication_form = AuthenticationForm

# logout
class LogoutView(auth_views.LogoutView):
     next_page = '/'

# MQTT login views

class MQTTLoginView(CsrfExemptMixin,
                    FormView):
    template_name = 'login/mqtt_login.html'
    form_class = AuthenticationForm
    
    def form_invalid(self, form):
        return HttpResponseForbidden()
    
    def form_valid(self, form):
        return HttpResponse('OK')
    
class MQTTSuperuserView(CsrfExemptMixin,
                        View):
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        data = {}
        if hasattr(request, 'POST'):
            data = request.POST
        elif hasattr(request, 'DATA'):
            data = request.DATA
        try:
            if User.objects.get(username=data.get('username'),
                                is_active=True).is_superuser:
                return HttpResponse('OK')
            
        except User.DoesNotExist:
            pass
        
        return HttpResponseForbidden()

class MQTTAclView(CsrfExemptMixin,
                  View):
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        data = {}
        if hasattr(request, 'POST'):
            data = request.POST
        elif hasattr(request, 'DATA'):
            data = request.DATA
        allow = False

        # Check permissions
        username = data.get('username')
        acc = int(data.get('acc')) # 1 == sub, 2 == pub

        # get topic and remove first '/'
        topic = data.get('topic').split('/')
        if len(topic) > 0 and topic[0] == '':
            del topic[0]

        try:
            
            # get user
            user = User.objects.get(username=data.get('username'),
                                    is_active=True)

            #print('topic = {}'.format(topic))
            #print('user = {}'.format(user))
            #print('user.hospitals = {}'.format(user.hospitals.all()))

            if acc == 1:
                
                # permission to subscribe:

                #  - user/*username*/error
                #  - user/*username*/profile
                if (len(topic) == 3 and
                    topic[0] == 'user' and
                    topic[1] == user.username):

                    if (topic[2] == 'profile' or
                        topic[2] == 'error'):
                        
                        return HttpResponse('OK')

                #  - hospital/+/data
                #  - hospital/+/metadata
                #  - hospital/+/equipment/+/data
                elif (len(topic) >= 3 and
                      topic[0] == 'hospital'):
                    
                    hospital_id = int(topic[1])
                    #print('hospital_id = {}'.format(hospital_id))

                    # is user authorized?
                    try:
                        
                        perm = user.profile.hospitals.get(hospital=hospital_id)
            
                        if (perm.can_read and
                            ((len(topic) == 3 and topic[2] == 'data') or
                             (len(topic) == 3 and topic[2] == 'metadata') or
                             (len(topic) == 5 and topic[2] == 'equipment'
                                              and topic[4] == 'data'))):
                        
                            return HttpResponse('OK')

                    except ObjectDoesNotExist:
                        pass

                #  - ambulance/+/data
                elif (len(topic) == 3 and
                      topic[0] == 'ambulance' and
                      topic[2] == 'data'):
                    
                    ambulance_id = int(topic[1])
                    #print('ambulance_id = {}'.format(ambulance_id))

                    # is user authorized?
                    try:
                        
                        perm = user.profile.ambulances.get(ambulance=ambulance_id)
            
                        if perm.can_read:
                        
                            return HttpResponse('OK')

                    except ObjectDoesNotExist:
                        pass
                    
            elif acc == 2:
                
                # permission to publish:

                if (len(topic) >= 3 and
                    topic[0] == 'user' and
                    topic[1] == user.username):

                    #  - user/*username*/error
                    if (len(topic) == 3 and
                        topic[2] == 'error'):
                        
                        return HttpResponse('OK')
                    
                    #  - user/*username*/ambulance/+/data
                    elif (len(topic) == 5 and
                        topic[2] == 'ambulance' and
                        topic[4] == 'data'):

                        ambulance_id = int(topic[3])
                        #print('ambulance_id = {}'.format(ambulance_id))

                        # is user authorized?
                        try:
                        
                            perm = user.profile.ambulances.get(ambulance=ambulance_id)
            
                            if perm.can_write:
                        
                                return HttpResponse('OK')

                        except ObjectDoesNotExist:
                            pass

                    #  - user/*username*/hospital/+/data
                    #  - user/*username*/hospital/+/equipment/+/data
                    elif ((len(topic) == 5 and
                           topic[2] == 'hospital' and
                           topic[4] == 'data') or
                          (len(topic) == 7 and
                           topic[2] == 'hospital' and
                           topic[4] == 'equipment' and
                           topic[6] == 'data')):

                        hospital_id = int(topic[3])
                        #print('hospital_id = {}'.format(hospital_id))

                        # is user authorized?
                        try:
                        
                            perm = user.profile.hospitals.get(hospital=hospital_id)
            
                            if perm.can_write:
                        
                                return HttpResponse('OK')

                        except ObjectDoesNotExist:
                            pass
                        
        except User.DoesNotExist:
            pass
        
        return HttpResponseForbidden()

from rest_framework.views import APIView
from rest_framework.response import Response
import string, random
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

class MQTTPassword(APIView):
    """
    Retrieve password to use with MQTT
    """

    @staticmethod
    def generate_password(size = 20,
                          chars = (string.ascii_letters +
                                   string.digits +
                                   string.punctuation)):
        return (''.join(random.choice(chars) for _ in range(size)))
    
    def get(self, request, format=None):
        """
        Generate password if one does not exist or is invalid and stores a
        hash in the database. Users in possesion of this password will
        be able to login with it only through MQTT.
        """

        # retrieve user
        user = request.user
        
        try:

            # Retrieve current password
            pwd = TemporaryPassword.objects.get(user = user.id)
            password = pwd.password
            valid_until = pwd.created_on + timedelta(seconds=120)
            print('created = {}, valid_until = {}, now = {}'.format(pwd.created_on,
                                                                    valid_until,
                                                                    timezone.now()))

            # Invalidate password if it is expired
            if timezone.now() > valid_until:
                password = None

        except ObjectDoesNotExist:

            pwd = None
            password = None

        if password is None:
            
            # Generate password
            password = self.generate_password()

            if pwd is None:
                
                # create password
                pwd = TemporaryPassword(user = user,
                                        password = password)

            else:

                # update password
                pwd.password = password

            # save password
            pwd.save()

        # Return password hash
        password_hash = make_password(password=password)
            
        return Response(password_hash)
