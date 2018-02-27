import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from django.views.generic import TemplateView, ListView, \
    DetailView, CreateView, UpdateView

from .models import Ambulance, AmbulanceCapability, AmbulanceStatus, \
    Call

from .forms import AmbulanceCreateForm, AmbulanceUpdateForm

from .serializers import AmbulanceSerializer

from emstrack.mixins import BasePermissionMixin

from django.template.defaulttags import register

from emstrack.views import get_page_links


# Ambulance status filter

@register.filter
def get_status(status):
    return AmbulanceStatus[status].value


# Django views

class AmbulancePermissionMixin(BasePermissionMixin):

    filter_field = 'id'
    profile_field = 'ambulances'
    queryset = Ambulance.objects.all()


class AmbulanceActionMixin:

    @property
    def success_message(self):
        return NotImplemented

    def form_valid(self, form):

        # add message
        messages.info(self.request, self.success_message)

        # add updated_by to form and save
        form.instance.updated_by = self.request.user

        # call super
        return super().form_valid(form)


class AmbulanceDetailView(LoginRequiredMixin,
                          AmbulancePermissionMixin,
                          DetailView):

    model = Ambulance
    
    def get_context_data(self, **kwargs):
        # add paginated updates to context

        # call supper
        context = super().get_context_data(**kwargs)

        # query
        updates_query = self.object.ambulanceupdate_set.order_by('-timestamp')

        # get current page
        page = self.request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', 25)

        # paginate
        paginator = Paginator(updates_query, page_size)
        try:
            updates = paginator.page(page)
        except PageNotAnInteger:
            updates = paginator.page(1)
        except EmptyPage:
            updates = paginator.page(paginator.num_pages)

        # TODO: Return better page links for navigation

        context['updates'] = updates
        context['page_links'] = get_page_links(self.request, updates)


        # add ambulance_status
        context['ambulance_status'] = {m.name: m.value
                                       for m in AmbulanceStatus}

        return context


class AmbulanceListView(LoginRequiredMixin,
                        AmbulancePermissionMixin,
                        ListView):
    
    model = Ambulance;


class AmbulanceCreateView(LoginRequiredMixin,
                          AmbulancePermissionMixin,
                          AmbulanceActionMixin,
                          CreateView):
    
    model = Ambulance
    form_class = AmbulanceCreateForm

    def get_success_url(self):
        return self.object.get_absolute_url()
    

class AmbulanceUpdateView(LoginRequiredMixin,
                          AmbulancePermissionMixin,
                          AmbulanceActionMixin,
                          UpdateView):
    
    model = Ambulance
    form_class = AmbulanceUpdateForm

    def get_success_url(self):
        return self.object.get_absolute_url()


class AmbulanceMap(TemplateView):
    template_name = 'ambulance/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ambulance_status'] = {m.name: m.value
                                       for m in AmbulanceStatus}
        context['ambulance_capability'] = {m.name: m.value
                                           for m in AmbulanceCapability}
        context['broker_websockets_host'] = settings.MQTT['BROKER_WEBSOCKETS_HOST']
        context['broker_websockets_port'] = settings.MQTT['BROKER_WEBSOCKETS_PORT']
        context['client_id'] = 'javascript_client_' + uuid.uuid4().hex
        return context
    

# NEED REVISING
    
# Call list page
class CallView(ListView):
    model = Call
    template_name = 'ambulance/dispatch_list.html'
    context_object_name = "ambulance_call"


# Admin page
class AdminView(ListView):
    model = Call
    template_name = 'ambulance/dispatch_list.html'
    context_object_name = "ambulance_call"
    
# # AmbulanceStatus list page
# class AmbulanceStatusCreateView(CreateView):
#     model = AmbulanceStatus
#     context_object_name = "ambulance_status_form"
#     form_class = AmbulanceStatusCreateForm
#     success_url = reverse_lazy('status')

#     def get_context_data(self, **kwargs):
#         context = super(AmbulanceStatusCreateView, self).get_context_data(**kwargs)
#         context['statuses'] = AmbulanceStatus.objects.all().order_by('id')
#         return context


# # AmbulanceStatus update page
# class AmbulanceStatusUpdateView(UpdateView):
#     model = AmbulanceStatus
#     form_class = AmbulanceStatusUpdateForm
#     template_name = 'ambulances/ambulance_status_edit.html'
#     success_url = reverse_lazy('status')

#     def get_object(self, queryset=None):
#         obj = AmbulanceStatus.objects.get(id=self.kwargs['pk'])
#         return obj

#     def get_context_data(self, **kwargs):
#         context = super(AmbulanceStatusUpdateView, self).get_context_data(**kwargs)
#         context['id'] = self.kwargs['pk']
#         return context


# # Ambulance map page
# class AmbulanceMap(views.JSONResponseMixin, views.AjaxResponseMixin, ListView):
#     template_name = 'ambulances/ambulance_map.html'

#     def get_queryset(self):
#         return Ambulance.objects.all()
