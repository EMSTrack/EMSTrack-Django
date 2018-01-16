from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, \
    DetailView, CreateView, UpdateView

from .models import Ambulance, Call, Base, AmbulanceRoute

from .forms import AmbulanceCreateForm, AmbulanceUpdateForm

from .serializers import AmbulanceSerializer

from util.mixins import BasePermissionMixin

# Django views

class AmbulancePermissionMixin(BasePermissionMixin):

    filter_field = 'id'
    profile_field = 'ambulances'
    profile_values = 'ambulance_id'
    queryset = Ambulance.objects.all()

class AmbulanceActionMixin:

    fields = [ 'identifier', 'capability', 'status', 'comment', 'location' ]

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
         context['ambulance_list'] = Ambulance.objects.all()
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
