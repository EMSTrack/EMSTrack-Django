import django_filters.rest_framework
#from django.core.urlresolvers import reverse_lazy
from django.urls import reverse_lazy
from django.http import Http404
from django.shortcuts import get_object_or_404

from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from .models import Ambulance, Call, Base, AmbulanceRoute

from .forms import AmbulanceCreateForm, AmbulanceUpdateForm

from .serializers import AmbulanceSerializer

# Django views

class AmbulanceActionMixin:

    fields = [ 'identifier', 'capability', 'status', 'comment' ]

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
                          DetailView):
    model = Ambulance
    
class AmbulanceListView(LoginRequiredMixin,
                        ListView):
    model = Ambulance

class AmbulanceCreateView(LoginRequiredMixin,
                          HospitalActionMixin,
                          CreateView):
    model = Ambulance

    def get_success_url(self):
        return self.object.get_absolute_url()
    
class AmbulanceUpdateView(LoginRequiredMixin,
                          HospitalActionMixin,
                          UpdateView):
    model = Ambulance

    def get_success_url(self):
        return self.object.get_absolute_url()

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


# Ambulance map page
class AmbulanceMap(views.JSONResponseMixin, views.AjaxResponseMixin, ListView):
    template_name = 'ambulances/ambulance_map.html'

    def get_queryset(self):
        return Ambulance.objects.all()
