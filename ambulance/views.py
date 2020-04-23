import uuid

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, \
    DetailView, CreateView, UpdateView, FormView
from django.views.generic.detail import BaseDetailView

from django.utils.translation import ugettext_lazy as _

from drf_extra_fields.geo_fields import PointField

from ambulance.permissions import CallPermissionMixin
from ambulance.resources import AmbulanceResource, CallRadioCodeResource, CallPriorityCodeResource, \
    CallPriorityClassificationResource

from equipment.mixins import EquipmentHolderCreateMixin, EquipmentHolderUpdateMixin

from emstrack.models import defaults
from emstrack.mixins import BasePermissionMixin, UpdatedByMixin, ExportModelMixin, ImportModelMixin, \
    ProcessImportModelMixin, PaginationViewMixin
from emstrack.views import get_page_links, get_page_size_links

from login.models import can_sms_notifications

from .models import Ambulance, AmbulanceCapability, AmbulanceStatus, \
    Call, Location, LocationType, CallStatus, AmbulanceCallStatus, \
    CallPriority, AmbulanceStatusOrder, AmbulanceCapabilityOrder, CallStatusOrder, CallPriorityOrder, LocationTypeOrder, \
    AmbulanceOnline, AmbulanceOnlineOrder, CallRadioCode, CallPriorityCode, WaypointStatus, WaypointStatusOrder, \
    CallPriorityClassification

from .forms import AmbulanceCreateForm, AmbulanceUpdateForm, LocationAdminCreateForm, LocationAdminUpdateForm



from emstrack.views import get_page_links, get_page_size_links


# Ambulance views

class AmbulancePermissionMixin(BasePermissionMixin):
    filter_field = 'id'
    profile_field = 'ambulances'
    queryset = Ambulance.objects.all()


class AmbulanceDetailView(LoginRequiredMixin,
                          SuccessMessageMixin,
                          UpdatedByMixin,
                          AmbulancePermissionMixin,
                          DetailView):
    model = Ambulance

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['ambulance_status'] = {m.name: m.value
                                       for m in AmbulanceStatus}
        context['ambulance_status_order'] = [m.name for m in AmbulanceStatusOrder]
        context['location_type'] = {m.name: m.value
                                    for m in LocationType}
        context['location_type_order'] = [m.name for m in LocationTypeOrder]

        context['translation_table'] = {
        }

        return context


class AmbulanceListView(PaginationViewMixin,
                        LoginRequiredMixin,
                        AmbulancePermissionMixin,
                        ListView):
    
    model = Ambulance
    ordering = ['identifier']


class AmbulanceCreateView(LoginRequiredMixin,
                          SuccessMessageMixin,
                          UpdatedByMixin,
                          EquipmentHolderCreateMixin,
                          AmbulancePermissionMixin,
                          CreateView):
    model = Ambulance
    form_class = AmbulanceCreateForm

    def get_success_message(self, cleaned_data):
        return "Successfully created ambulance '{}'".format(cleaned_data['identifier'])

    def get_success_url(self):
        return self.object.get_absolute_url()
    

class AmbulanceUpdateView(LoginRequiredMixin,
                          SuccessMessageMixin,
                          UpdatedByMixin,
                          EquipmentHolderUpdateMixin,
                          AmbulancePermissionMixin,
                          UpdateView):
    model = Ambulance
    form_class = AmbulanceUpdateForm

    def get_success_message(self, cleaned_data):
        return "Successfully updated ambulance '{}'".format(cleaned_data['identifier'])

    def get_success_url(self):
        return self.object.get_absolute_url()


# Ambulance css information
AmbulanceCSS = {

    'UK': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_blue.svg',
            'iconSize': [15, 30],
        },
        'class': 'primary'
    },
    'AV': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_green.svg',
            'iconSize': [15, 30],
        },
        'class': 'success'
    },
    'OS': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_gray.svg',
            'iconSize': [15, 30],
        },
        'class': 'secondary'
    },

    'PB': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_red.svg',
            'iconSize': [15, 30],
        },
        'class': 'danger'
    },
    'AP': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_orange.svg',
            'iconSize': [15, 30],
        },
        'class': 'warning'
    },

    'HB': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_red.svg',
            'iconSize': [15, 30],
        },
        'class': 'danger'
    },
    'AH': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_orange.svg',
            'iconSize': [15, 30],
        },
        'class': 'warning'
    },

    'BB': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_red.svg',
            'iconSize': [15, 30],
        },
        'class': 'danger'
    },
    'AB': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_orange.svg',
            'iconSize': [15, 30],
        },
        'class': 'warning'
    },


    'WB': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_red.svg',
            'iconSize': [15, 30],
        },
        'class': 'danger'
    },
    'AW': {
        'icon': {
            'iconUrl': '/static/icons/cars/ambulance_orange.svg',
            'iconSize': [15, 30],
        },
        'class': 'warning'
    }

}


# CallPriority css information
CallPriorityCSS = {
    'A': {
        'class': 'success',
        'html': 'A'
    },
    'B': {
        'class': 'yellow',
        'html': 'B'
    },
    'C': {
        'class': 'warning',
        'html': 'C'
    },
    'D': {
        'class': 'danger',
        'html': 'D'
    },
    'E': {
        'class': 'info',
        'html': 'E'
    },
    'O': {
        'class': 'secondary',
        'html': '&Omega;'
    }
}


class AmbulanceMap(TemplateView):
    template_name = 'ambulance/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ambulance_status'] = {m.name: m.value
                                       for m in AmbulanceStatus}
        context['ambulance_status_order'] = [m.name for m in AmbulanceStatusOrder]
        context['ambulance_capability'] = {m.name: m.value
                                           for m in AmbulanceCapability}
        context['ambulance_capability_order'] = [m.name for m in AmbulanceCapabilityOrder]
        context['ambulance_online'] = {m.name: m.value
                                           for m in AmbulanceOnline}
        context['ambulance_online_order'] = [m.name for m in AmbulanceOnlineOrder]
        context['location_type'] = {m.name: m.value
                                    for m in LocationType}
        context['location_type_order'] = [m.name for m in LocationTypeOrder]
        context['waypoint_status'] = {m.name: m.value
                                      for m in WaypointStatus}
        context['waypoint_status_order'] = [m.name for m in WaypointStatusOrder]
        context['call_status'] = {m.name: m.value
                                  for m in CallStatus}
        context['call_status_order'] = [m.name for m in CallStatusOrder]
        context['call_priority'] = {m.name: m.value
                                    for m in CallPriority}
        context['call_priority_order'] = [m.name for m in CallPriorityOrder]
        context['ambulancecall_status'] = {m.name: m.value
                                           for m in AmbulanceCallStatus}
        context['broker_websockets_host'] = settings.MQTT['BROKER_WEBSOCKETS_HOST']
        context['broker_websockets_port'] = settings.MQTT['BROKER_WEBSOCKETS_PORT']
        context['client_id'] = 'javascript_client_' + uuid.uuid4().hex
        context['ambulance_css'] = AmbulanceCSS
        context['call_priority_css'] = CallPriorityCSS
        context['map_provider'] = {'provider': settings.MAP_PROVIDER, 'access_token': settings.MAP_PROVIDER_TOKEN}

        context['radio_code_list'] = CallRadioCode.objects.all().order_by('code')
        context['priority_code_list'] = CallPriorityCode.objects.all().order_by('prefix', 'priority', 'suffix')
        context['sms_notifications_list'] = can_sms_notifications()

        default_values = defaults.copy()
        default_values['location'] = PointField().to_representation(defaults['location'])
        context['defaults'] = default_values

        context['translation_table'] = {
            "Age": _("Age"),
            "Name": _("Name"),
            "Radio Code": _("Radio Code"),
            "Priority Code": _("Priority Code"),
            "Priority Classification": _("Priority Classification"),
            "Alert": _("Alert"),
            "Attention": _("Attention"),
            "Invalid radio code": _("Invalid radio code"),
            "Invalid priority code": _("Invalid priority code"),
            "Please select the priority": _("Please select the priority"),
            "Please dispatch at least one ambulance": _("Please dispatch at least one ambulance"),
            "Blank name": _("Blank name"),
            "Can only dispatch available ambulances!": _("Can only dispatch available ambulances!"),
            "Could not update ambulance status": _("Could not update ambulance status"),
            "'%s' is now '%s'": _("'%s' is now '%s'"),
            "Do you want to abort call %d?": _("Do you want to abort call %d?"),
            "Do you want to modify ambulance <strong>%s</strong> status to <strong>%s</strong>?":
                _("Do you want to modify ambulance <strong>%s</strong> status to <strong>%s</strong>?"),
            "Patients": _("Patients"),
            "No patient names are available.": _("No patient names are available."),
            "Details": _("Details"),
            "Notes": _("Notes"),
            "Enter new note": _("Enter new note"),
            "Send SMS notifications?": _("Send SMS notifications?"),
            "Description": _("Description"),
            "Describe the incident": _("Describe the incident"),
            "SMS Notifications": _("SMS Notifications"),
            "Do you want to save %s?": _("Do you want to save the %s?"),
            "Select username": _("Select username"),
            "the call": _("the call"),
            "the patients": _("the patients"),
            "Save": _("Save"),
            "Cancel": _("Cancel"),
            "Roads": _("Roads"),
            "Satellite": _("Satellite"),
            "Hybrid": _("Hybrid"),
            "Waypoints": _("Waypoints"),
            "Type": _("Type"),
            "Status": _("Status"),
            "Address": _("Address"),
            "Please select": _("Please select"),
            "Ok": _("Ok"),
            "Close": _("Close"),
            "Please confirm that you want to skip the current waypoint.": _("Please confirm that you want to skip the "
                                                                            "current waypoint."),
            "Do you want to save the modified waypoints?": _("Do you want to save the modified waypoints?"),
            "Do you want to save the modified patients?": _("Do you want to save the modified patients?")
        }

        return context


# Locations

class LocationAdminListView(ListView):
    model = Location

    def get_context_data(self, **kwargs):

        # add paginated ended calls to context
        
        # call supper
        context = super().get_context_data(**kwargs)
        
        # query all calls
        queryset = self.get_queryset()
        
        # filter
        context['base_list'] = queryset.filter(type=LocationType.b.name).order_by('name')
        context['other_list'] = queryset.filter(type=LocationType.o.name).order_by('name')
        context['aed_list'] = queryset.filter(type=LocationType.a.name).order_by('name')

        # query ended and paginate
        incident_query = queryset.filter(type=LocationType.i.name).order_by('-updated_on')

        # get current page
        page = self.request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', 25)
        page_sizes = [25, 50, 100]

        # paginate
        paginator = Paginator(incident_query, page_size)
        try:
            incident = paginator.page(page)
        except PageNotAnInteger:
            incident = paginator.page(1)
        except EmptyPage:
            incident = paginator.page(paginator.num_pages)

        context['incident_list'] = incident
        context['page_links'] = get_page_links(self.request, incident)
        context['page_size_links'] = get_page_size_links(self.request, incident, page_sizes)
        context['page_size'] = int(page_size)

        return context


class LocationAdminDetailView(DetailView):
    model = Location
    queryset = Location.objects.exclude(type=LocationType.h.name).exclude(type=LocationType.w.name)


class LocationAdminCreateView(SuccessMessageMixin,
                              UpdatedByMixin,
                              CreateView):
    model = Location
    form_class = LocationAdminCreateForm

    def get_success_message(self, cleaned_data):
        return "Successfully created location '{}'".format(cleaned_data['name'])

    def get_success_url(self):
        return self.object.get_absolute_url()


class LocationAdminUpdateView(SuccessMessageMixin,
                              UpdatedByMixin,
                              UpdateView):
    model = Location
    form_class = LocationAdminUpdateForm

    def get_success_message(self, cleaned_data):
        return "Successfully updated location '{}'".format(cleaned_data['name'])

    def get_success_url(self):
        return self.object.get_absolute_url()


# Calls

# Call ListView
class CallListView(LoginRequiredMixin,
                   CallPermissionMixin,
                   ListView):
    model = Call

    def get_context_data(self, **kwargs):

        # add paginated ended calls to context

        # call supper
        context = super().get_context_data(**kwargs)

        # query all calls
        queryset = self.get_queryset()

        # filter
        context['pending_list'] = queryset.filter(status=CallStatus.P.name).order_by('pending_at')
        context['started_list'] = queryset.filter(status=CallStatus.S.name).order_by('-started_at')

        # query ended and paginate
        ended_calls_query = queryset.filter(status=CallStatus.E.name).order_by('-ended_at')

        # get current page
        page = self.request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', 25)
        page_sizes = [25, 50, 100]

        # paginate
        paginator = Paginator(ended_calls_query, page_size)
        try:
            ended_calls = paginator.page(page)
        except PageNotAnInteger:
            ended_calls = paginator.page(1)
        except EmptyPage:
            ended_calls = paginator.page(paginator.num_pages)

        context['ended_list'] = ended_calls
        context['page_links'] = get_page_links(self.request, ended_calls)
        context['page_size_links'] = get_page_size_links(self.request, ended_calls, page_sizes)
        context['page_size'] = int(page_size)

        return context


# Call DetailView
class CallDetailView(LoginRequiredMixin,
                     CallPermissionMixin,
                     SuccessMessageMixin,
                     UpdatedByMixin,
                     DetailView):
    model = Call

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location_type'] = {m.name: m.value
                                       for m in LocationType}
        context['ambulance_status'] = {m.name: m.value
                                       for m in AmbulanceStatus}
        context['map_provider'] = {'provider': settings.MAP_PROVIDER, 'access_token': settings.MAP_PROVIDER_TOKEN}

        context['translation_table'] = {
            "Abort Call": _("Abort Call"),
            "Are you sure?": _("Are you sure?"),
        }

        return context

    def get_success_url(self):
        return self.object.get_absolute_url()


# Call abort view
class CallAbortView(LoginRequiredMixin,
                    CallPermissionMixin,
                    SuccessMessageMixin,
                    BaseDetailView):
    model = Call

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get(self, request, *args, **kwargs):

        # Make sure user is super, staff, or dispatcher.
        user = request.user
        if not (user.is_superuser or user.is_staff or user.userprofile.is_dispatcher):
            return HttpResponseForbidden()

        # get call object
        self.object = self.get_object()

        # abort call
        self.object.abort()

        return redirect('ambulance:call_list')


# RadioCode and PriorityCode views

class CallRadioCodeListView(PaginationViewMixin,
                            ListView):
    model = CallRadioCode
    ordering = ['code']


class CallPriorityCodeListView(PaginationViewMixin,
                               ListView):
    model = CallPriorityCode
    ordering = ['prefix', 'priority', 'suffix']


class CallPriorityClassificationListView(PaginationViewMixin,
                                         ListView):
    model = CallPriorityClassification
    ordering = ['id']


# Ambulance import and export

class AmbulanceExportView(ExportModelMixin,
                          View):
    model = Ambulance
    resource_class = AmbulanceResource


class AmbulanceImportView(ImportModelMixin,
                          TemplateView):
    model = Ambulance
    resource_class = AmbulanceResource

    process_import_url = 'ambulance:process-import-ambulance'
    import_breadcrumbs = {'ambulance:list': _("Ambulances")}


class AmbulanceProcessImportView(SuccessMessageMixin,
                                 ProcessImportModelMixin,
                                 FormView):
    model = Ambulance
    resource_class = AmbulanceResource

    success_message = _('Successfully imported ambulances')
    success_url = reverse_lazy('ambulance:list')

    import_breadcrumbs = {'ambulance:list': _("Ambulances")}


# CallRadioCode import and export

class CallRadioCodeExportView(ExportModelMixin,
                              View):
    model = CallRadioCode
    resource_class = CallRadioCodeResource


class CallRadioCodeImportView(ImportModelMixin,
                              TemplateView):
    model = CallRadioCode
    resource_class = CallRadioCodeResource

    process_import_url = 'ambulance:process-import-radio-code'
    import_breadcrumbs = {'ambulance:radio-code-list': _("Radio Codes")}


class CallRadioCodeProcessImportView(SuccessMessageMixin,
                                     ProcessImportModelMixin,
                                     FormView):
    model = CallRadioCode
    resource_class = CallRadioCodeResource

    success_message = _('Successfully imported call radio codes')
    success_url = reverse_lazy('ambulance:radio-code-list')

    import_breadcrumbs = {'ambulancs:radio-code-list': _("Radio Codes")}


# CallPriorityCode import and export

class CallPriorityCodeExportView(ExportModelMixin,
                                 View):
    model = CallPriorityCode
    resource_class = CallPriorityCodeResource


class CallPriorityCodeImportView(ImportModelMixin,
                                 TemplateView):
    model = CallPriorityCode
    resource_class = CallPriorityCodeResource

    process_import_url = 'ambulance:process-import-priority-code'
    import_breadcrumbs = {'ambulance:priority-code-list': _("Priority Codes")}


class CallPriorityCodeProcessImportView(SuccessMessageMixin,
                                        ProcessImportModelMixin,
                                        FormView):
    model = CallPriorityCode
    resource_class = CallPriorityCodeResource

    success_message = _('Successfully imported call priority codes')
    success_url = reverse_lazy('ambulance:priority-code-list')

    import_breadcrumbs = {'ambulancs:priority-code-list': _("Priority Codes")}


# CallPriorityClassification import and export

class CallPriorityClassificationExportView(ExportModelMixin,
                                           View):
    model = CallPriorityClassification
    resource_class = CallPriorityClassificationResource


class CallPriorityClassificationImportView(ImportModelMixin,
                                           TemplateView):
    model = CallPriorityClassification
    resource_class = CallPriorityClassificationResource

    process_import_url = 'ambulance:process-import-priority-classification'
    import_breadcrumbs = {'ambulance:priority-classification-list': _("Priority Classifications")}


class CallPriorityClassificationProcessImportView(SuccessMessageMixin,
                                                  ProcessImportModelMixin,
                                                  FormView):
    model = CallPriorityClassification
    resource_class = CallPriorityClassificationResource

    success_message = _('Successfully imported call priority classifications')
    success_url = reverse_lazy('ambulance:priority-classification-list')

    import_breadcrumbs = {'ambulancs:priority-classification-list': _("Priority Classifications")}
