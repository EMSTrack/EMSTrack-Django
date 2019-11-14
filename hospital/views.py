from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, CreateView, TemplateView, FormView
from django.utils.translation import ugettext_lazy as _

from equipment.mixins import EquipmentHolderCreateMixin, EquipmentHolderUpdateMixin
from hospital.resources import HospitalResource
from .models import Hospital

from .forms import HospitalCreateForm, HospitalUpdateForm

from emstrack.mixins import BasePermissionMixin, UpdatedByMixin, PaginationViewMixin, ExportModelMixin, \
    ImportModelMixin, ProcessImportModelMixin


# Django views

class HospitalPermissionMixin(BasePermissionMixin):
    filter_field = 'id'
    profile_field = 'hospitals'
    queryset = Hospital.objects.all()


class HospitalCreateView(LoginRequiredMixin,
                         SuccessMessageMixin,
                         UpdatedByMixin,
                         EquipmentHolderCreateMixin,
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
                         EquipmentHolderUpdateMixin,
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


class HospitalListView(PaginationViewMixin,
                       LoginRequiredMixin,
                       HospitalPermissionMixin,
                       ListView):
    model = Hospital
    ordering = ['name']


# Hospital import and export

class HospitalExportView(ExportModelMixin,
                         View):
    model = Hospital
    resource_class = HospitalResource


class HospitalImportView(ImportModelMixin,
                         TemplateView):
    model = Hospital
    resource_class = HospitalResource

    process_import_url = 'hospital:process-import-hospital'
    import_breadcrumbs = {'hospital:list': _("Hospitals")}


class HospitalProcessImportView(SuccessMessageMixin,
                                ProcessImportModelMixin,
                                FormView):
    model = Hospital
    resource_class = HospitalResource

    success_message = _('Successfully imported hospitals')
    success_url = reverse_lazy('hospital:list')

    import_breadcrumbs = {'hospital:list': _("Hospitals")}
