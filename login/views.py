import logging
import random
import string
from datetime import timedelta

from braces.views import CsrfExemptMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group
from django.contrib.messages.views import SuccessMessageMixin
from django.core import management
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http.response import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView, CreateView
from drf_extra_fields.geo_fields import PointField
from extra_views import InlineFormSet, CreateWithInlinesView, UpdateWithInlinesView
from rest_framework.response import Response
from rest_framework.views import APIView

from ambulance.models import AmbulanceStatus, AmbulanceCapability, LocationType
from emstrack.mixins import SuccessMessageWithInlinesMixin
from emstrack.models import defaults
from hospital.models import EquipmentType
from login import permissions
from .forms import MQTTAuthenticationForm, AuthenticationForm, SignupForm, \
    UserAdminCreateForm, UserAdminUpdateForm, \
    GroupAdminUpdateForm, \
    GroupProfileAdminForm, GroupAmbulancePermissionAdminForm, GroupHospitalPermissionAdminForm, \
    UserAmbulancePermissionAdminForm, \
    UserHospitalPermissionAdminForm, RestartForm
from .models import TemporaryPassword, \
    UserAmbulancePermission, UserHospitalPermission, \
    GroupProfile, GroupAmbulancePermission, \
    GroupHospitalPermission
from .permissions import get_permissions

logger = logging.getLogger(__name__)


# signup

class SignupView(FormView):
    template_name = 'index.html'
    form_class = SignupForm

    def form_valid(self, form):
        # TODO: Automatic signup could send an email to prospective user
        # then notify administrator of new user
        # form.send_email()
        # return super().form_valid(form)
        # for now abort and alert user
        form.add_error(None, 'We are sorry but EMSTrack is not accepting new users at this point.');
        return super().form_invalid(form);


# login

class LoginView(auth_views.LoginView):
    template_name = 'index.html'
    authentication_form = AuthenticationForm


# logout

class LogoutView(auth_views.LogoutView):
    next_page = '/'


# Groups

class GroupAdminListView(ListView):
    model = Group
    template_name = 'login/group_list.html'


class GroupAdminDetailView(DetailView):
    model = Group
    template_name = 'login/group_detail.html'
    fields = ['name']

    def get_context_data(self, **kwargs):

        # call super to retrieve object
        context = super().get_context_data(**kwargs)

        # retrieve permissions and add to context
        context['ambulance_list'] = self.object.groupambulancepermission_set.all()
        context['hospital_list'] = self.object.grouphospitalpermission_set.all()

        # retrieve users and add to context
        context['user_list'] = self.object.user_set.all()

        return context


class GroupProfileAdminInline(InlineFormSet):
    model = GroupProfile
    form_class = GroupProfileAdminForm
    min_num = 1
    max_num = 1
    extra = 0
    can_delete = False


class GroupAmbulancePermissionAdminInline(InlineFormSet):
    model = GroupAmbulancePermission
    form_class = GroupAmbulancePermissionAdminForm
    extra = 1


class GroupHospitalPermissionAdminInline(InlineFormSet):
    model = GroupHospitalPermission
    form_class = GroupHospitalPermissionAdminForm
    extra = 1


class GroupAdminCreateView(SuccessMessageMixin, CreateView):
    model = Group
    fields = ['name']
    template_name = 'login/group_create.html'

    def get_success_message(self, cleaned_data):
        return "Successfully created group '{}'".format(cleaned_data['name'])

    def get_success_url(self):
        return self.object.groupprofile.get_absolute_url()


class GroupAdminUpdateView(SuccessMessageWithInlinesMixin, UpdateWithInlinesView):
    model = Group
    template_name = 'login/group_form.html'
    form_class = GroupAdminUpdateForm
    inlines = [GroupProfileAdminInline,
               GroupAmbulancePermissionAdminInline,
               GroupHospitalPermissionAdminInline]

    def get_success_message(self, cleaned_data):
        return "Successfully updated group '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.groupprofile.get_absolute_url()


# Users

class UserAdminListView(ListView):
    model = User
    template_name = 'login/user_list.html'


class UserAdminDetailView(DetailView):
    model = User
    template_name = 'login/user_detail.html'
    fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']

    def get_context_data(self, **kwargs):

        # call super to retrieve object
        context = super().get_context_data(**kwargs)

        # retrieve permissions and add to context
        context['ambulance_list'] = self.object.userambulancepermission_set.all()
        context['hospital_list'] = self.object.userhospitalpermission_set.all()

        # retrieve groups and add to context
        context['group_list'] = self.object.groups.all()

        return context


class UserAmbulancePermissionAdminInline(InlineFormSet):
    model = UserAmbulancePermission
    form_class = UserAmbulancePermissionAdminForm
    extra = 1


class UserHospitalPermissionAdminInline(InlineFormSet):
    model = UserHospitalPermission
    form_class = UserHospitalPermissionAdminForm
    extra = 1


class UserAdminCreateView(SuccessMessageWithInlinesMixin, CreateWithInlinesView):
    model = User
    template_name = 'login/user_form.html'
    form_class = UserAdminCreateForm
    inlines = [UserAmbulancePermissionAdminInline,
               UserHospitalPermissionAdminInline]

    def get_success_message(self, cleaned_data):
        return "Successfully created user '{}'".format(self.object.username)

    def get_success_url(self):
        return self.object.userprofile.get_absolute_url()


class UserAdminUpdateView(SuccessMessageWithInlinesMixin, UpdateWithInlinesView):
    model = User
    template_name = 'login/user_form.html'
    form_class = UserAdminUpdateForm
    inlines = [UserAmbulancePermissionAdminInline,
               UserHospitalPermissionAdminInline]

    def get_success_message(self, cleaned_data):
        return "Successfully updated user '{}'".format(self.object.username)

    def get_success_url(self):
        return self.object.userprofile.get_absolute_url()


# Restart

class RestartView(FormView):
    form_class = RestartForm
    template_name = 'modal.html'

    def success_url(self):
        return self.request.GET.get('next', '/')

    def get_context_data(self, **kwargs):

        # call super to retrieve object
        context = super().get_context_data(**kwargs)

        # customize modal form
        context['title'] = 'EMSTrack restart'
        context['foreword'] = '<p>This command will invalidate the permission cache and reinitialize all settings</p>'
        context['afterword'] = '<p>Click OK if you would like to proceed or Cancel otherwise</p>'
        context['next'] = self.success_url()

        return context

    def form_valid(self, form):

        try:

            # invalidate permission cache
            permissions.cache_clear()

            # reseed mqtt
            management.call_command('mqttseed', verbosity=0)

            # call super form_valid
            return super().form_valid(form)

        except Exception as error:

            # add error to form
            form.add_error(None, error)

            # call super form_invalid
            return super().form_invalid(form);


# MQTT login views

class MQTTLoginView(CsrfExemptMixin,
                    FormView):
    """
    Authenticate user without logging in. 
    It is meant to be used for MQTT authentication only.
    """

    template_name = 'login/mqtt_login.html'
    form_class = MQTTAuthenticationForm

    def form_invalid(self, form):
        return HttpResponseForbidden()

    def form_valid(self, form):
        return HttpResponse('OK')


class MQTTSuperuserView(CsrfExemptMixin,
                        View):
    """
    Verify if user is superuser.
    """

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
    """
    Verify MQTT ACL permissions.
    """

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
        client_id = data.get('clientid')
        acc = int(data.get('acc'))  # 1 == sub, 2 == pub

        # get topic and remove first '/'
        topic = data.get('topic').split('/')
        if len(topic) > 0 and topic[0] == '':
            del topic[0]

        try:

            # get user
            user = User.objects.get(username=data.get('username'),
                                    is_active=True)

            if acc == 1:

                # permission to subscribe:

                #  - settings
                if (len(topic) == 1 and
                        topic[0] == 'settings'):

                    return HttpResponse('OK')

                #  - user/{username}/error
                #  - user/{username}/profile
                elif (len(topic) == 3 and
                      topic[0] == 'user' and
                      topic[1] == user.username):

                    if (topic[2] == 'profile' or
                            topic[2] == 'error'):
                        return HttpResponse('OK')

                #  - hospital/{hospital-id}/data
                #  - hospital/{hospital-id}/metadata
                #  - hospital/{hospital-id}/equipment/+/data
                elif (len(topic) >= 3 and
                      topic[0] == 'hospital'):

                    # get hospital id
                    hospital_id = int(topic[1])

                    # is user authorized?
                    try:

                        # perm = user.profile.hospitals.get(hospital=hospital_id)
                        can_read = get_permissions(user).check_can_read(hospital=hospital_id)

                        if (can_read and
                                ((len(topic) == 3 and topic[2] == 'data') or
                                 (len(topic) == 3 and topic[2] == 'metadata') or
                                 (len(topic) == 5 and topic[2] == 'equipment'
                                  and topic[4] == 'data'))):
                            return HttpResponse('OK')

                    except ObjectDoesNotExist:
                        pass

                #  - ambulance/{ambulance-id}/data
                elif (len(topic) == 3 and
                      topic[0] == 'ambulance' and
                      topic[2] == 'data'):

                    # get ambulance_id
                    ambulance_id = int(topic[1])

                    # is user authorized?
                    try:

                        # perm = user.profile.ambulances.get(ambulance=ambulance_id)
                        can_read = get_permissions(user).check_can_read(ambulance=ambulance_id)

                        if can_read:
                            return HttpResponse('OK')

                    except ObjectDoesNotExist:
                        pass

            elif acc == 2:

                # permission to publish:

                if (len(topic) >= 3 and
                        topic[0] == 'user' and
                        topic[1] == user.username):

                    #  - user/{username}/error
                    if (len(topic) == 3 and
                            topic[2] == 'error'):

                        return HttpResponse('OK')

                    #  - user/{username}/ambulance/{ambulance-id}/data
                    elif (len(topic) == 5 and
                          topic[2] == 'ambulance' and
                          topic[4] == 'data'):

                        # get ambulance_id
                        ambulance_id = int(topic[3])

                        # is user authorized?
                        try:

                            # perm = user.profile.ambulances.get(ambulance=ambulance_id)
                            can_write = get_permissions(user).check_can_write(ambulance=ambulance_id)

                            if can_write:
                                return HttpResponse('OK')

                        except ObjectDoesNotExist:
                            pass

                    #  - user/{username}/hospital/{hospital-id}/data
                    #  - user/{username}/hospital/{hospital-id}/equipment/+/data
                    elif ((len(topic) == 5 and
                           topic[2] == 'hospital' and
                           topic[4] == 'data') or
                          (len(topic) == 7 and
                           topic[2] == 'hospital' and
                           topic[4] == 'equipment' and
                           topic[6] == 'data')):

                        # get hospital_id
                        hospital_id = int(topic[3])

                        # is user authorized?
                        try:

                            # perm = user.profile.hospitals.get(hospital=hospital_id)
                            can_write = get_permissions(user).check_can_write(hospital=hospital_id)

                            if can_write:
                                return HttpResponse('OK')

                        except ObjectDoesNotExist:
                            pass

                    #  - user/{username}/client/{client-id}/status
                    elif (len(topic) == 5 and
                          topic[2] == 'client' and
                          topic[4] == 'status' and
                          topic[3] == client_id):

                        return HttpResponse('OK')

        except User.DoesNotExist:
            pass

        return HttpResponseForbidden()


class PasswordView(APIView):
    """
    Retrieve password to use with MQTT.
    """

    @staticmethod
    def generate_password(size=20,
                          chars=(string.ascii_letters +
                                 string.digits +
                                 string.punctuation)):
        return ''.join(random.choice(chars) for _ in range(size))

    def get(self, request, user__username=None):
        """
        Generate temporary password if one does not exist or is invalid.
        Stores password in the database and returns a hash. Users in 
        possesion of this hash will be able to login through MQTT. 
        Passwords are valid for 120 seconds. 
        A new hash is however returned every time.
        """

        # retrieve current user
        user = request.user

        # make sure user and username are the same
        if user.username != user__username:
            raise PermissionDenied()

        try:

            # Retrieve current password
            pwd = TemporaryPassword.objects.get(user=user.id)
            password = pwd.password
            valid_until = pwd.created_on + timedelta(seconds=120)

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
                pwd = TemporaryPassword(user=user,
                                        password=password)

            else:

                # update password
                pwd.password = password

            # save password
            pwd.save()

        # Return password hash
        password_hash = make_password(password=password)

        return Response(password_hash)


class SettingsView(APIView):
    """
    Retrieve current settings and options.
    """

    @staticmethod
    def get_settings():
        ambulance_status = {m.name: m.value for m in AmbulanceStatus}
        ambulance_capability = {m.name: m.value for m in AmbulanceCapability}
        equipment_type = {m.name: m.value for m in EquipmentType}
        location_type = {m.name: m.value for m in LocationType}

        # assemble all settings
        all_settings = {'ambulance_status': ambulance_status,
                        'ambulance_capability': ambulance_capability,
                        'equipment_type': equipment_type,
                        'location_type': location_type,
                        'defaults': defaults.copy()}

        # serialize defaults.location
        all_settings['defaults']['location'] = PointField().to_representation(defaults['location'])

        return all_settings

    def get(self, request, user__username=None):
        """
        Retrieve current settings and options.
        """

        return Response(self.get_settings())
