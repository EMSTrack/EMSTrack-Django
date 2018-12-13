from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, UpdateView, CreateView

from equipment.mixins import EquipmentHolderCreateMixin, EquipmentHolderUpdateMixin
from .models import Hospital

from .forms import HospitalCreateForm, HospitalUpdateForm

from emstrack.mixins import BasePermissionMixin, UpdatedByMixin


# Django views

class HospitalPermissionMixin(BasePermissionMixin):

    filter_field = 'id'
    profile_field = 'hospitals'
    queryset = Hospital.objects.all()


class HospitalCreateView(LoginRequiredMixin,
                         SuccessMessageMixin,
                         EquipmentHolderCreateMixin,
                         UpdatedByMixin,
                         HospitalPermissionMixin,
                         CreateView):
    model = Hospital
    form_class = HospitalCreateForm

    def get_success_message(self, cleaned_data):
        return "Successfully created hospital '{}'".format(cleaned_data['name'])

    def get_success_url(self):
        return self.object.get_absolute_url()


class HospitalUpdateView(LoginRequiredMixin,
                         SuccessMessageMixin,
                         EquipmentHolderUpdateMixin,
                         UpdatedByMixin,
                         HospitalPermissionMixin,
                         UpdateView):
    model = Hospital
    form_class = HospitalUpdateForm

    def get_success_message(self, cleaned_data):
        return "Successfully updated hospital '{}'".format(cleaned_data['name'])

    def get_success_url(self):
        return self.object.get_absolute_url()


class HospitalDetailView(LoginRequiredMixin,
                         HospitalPermissionMixin,
                         DetailView):

    model = Hospital


class HospitalListView(LoginRequiredMixin,
                       HospitalPermissionMixin,
                       ListView):

    model = Hospital
    ordering = ['name']
