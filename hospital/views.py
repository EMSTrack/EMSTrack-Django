from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from extra_views import InlineFormSet, CreateWithInlinesView, \
    UpdateWithInlinesView

from .models import Hospital, HospitalEquipment, Equipment

from .forms import HospitalCreateForm, HospitalUpdateForm

from emstrack.mixins import BasePermissionMixin, SuccessMessageWithInlinesMixin, UpdatedByWithInlinesMixin


# Django views


class HospitalPermissionMixin(BasePermissionMixin):

    filter_field = 'id'
    profile_field = 'hospitals'
    queryset = Hospital.objects.all()


class HospitalEquipmentInline(InlineFormSet):
    model = HospitalEquipment
    fields = ['equipment', 'value', 'comment']
    extra = 1


class HospitalCreateView(LoginRequiredMixin,
                         SuccessMessageWithInlinesMixin,
                         UpdatedByWithInlinesMixin,
                         HospitalPermissionMixin,
                         CreateWithInlinesView):
    model = Hospital
    inlines = [HospitalEquipmentInline]
    form_class = HospitalCreateForm

    def get_success_message(self, cleaned_data):
        return "Successfully created hospital '{}'".format(cleaned_data['name'])

    def get_success_url(self):
        return self.object.get_absolute_url()


class HospitalUpdateView(LoginRequiredMixin,
                         SuccessMessageWithInlinesMixin,
                         UpdatedByWithInlinesMixin,
                         HospitalPermissionMixin,
                         UpdateWithInlinesView):
    model = Hospital
    inlines = [HospitalEquipmentInline]
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


# HospitalEquipment

class EquipmentAdminListView(ListView):
    model = Equipment


class EquipmentAdminDetailView(DetailView):
    model = Equipment


class EquipmentAdminCreateView(SuccessMessageMixin,
                               CreateView):
    model = Equipment
    fields = ['name', 'etype']

    def get_success_message(self, cleaned_data):
        return "Successfully created equipment '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()


class EquipmentAdminUpdateView(SuccessMessageMixin,
                               UpdateView):
    model = Equipment
    fields = ['name', 'etype']

    def get_success_message(self, cleaned_data):
        return "Successfully updated equipment '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()
