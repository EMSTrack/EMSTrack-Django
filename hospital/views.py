from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, UpdateView, CreateView

from equipment.forms import EquipmentHolderUpdateForm
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
                         UpdatedByMixin,
                         HospitalPermissionMixin,
                         UpdateView):
    model = Hospital
    form_class = HospitalUpdateForm
    equipmentholder_form = EquipmentHolderUpdateForm

    def get_context_data(self, **kwargs):
        # Get the context
        context = super().get_context_data(**kwargs)

        # Add the equipmentholder form
        context['equipmentholder_form'] = self.equipmentholder_form(self.request.POST or None,
                                                                    instance=self.object.equipmentholder)

        return context

    def form_valid(self, form):
        # Get the equipmentholder form
        equipmentholder_form = self.equipmentholder_form(self.request.POST,
                                                         instance=self.object.equipmentholder)

        # Save form
        if equipmentholder_form.is_valid():
            equipmentholder_form.save(commit=False)

        # Call super
        return super().form_valid(form)

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
