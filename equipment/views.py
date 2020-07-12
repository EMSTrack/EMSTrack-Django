from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, FormView
from django.utils.translation import ugettext_lazy as _

from extra_views import InlineFormSet, UpdateWithInlinesView, CreateWithInlinesView

from emstrack.mixins import SuccessMessageWithInlinesMixin, UpdatedByWithInlinesMixin, BasePermissionMixin, \
    UpdatedByMixin, PaginationViewMixin, ExportModelMixin, ImportModelMixin, ProcessImportModelMixin
from equipment.forms import EquipmentHolderUpdateForm, EquipmentItemForm, EquipmentSetItemForm, EquipmentSetCreateForm, \
    EquipmentSetUpdateForm, EquipmentUpdateForm
from equipment.resources import EquipmentSetResource, EquipmentResource
from .models import EquipmentItem, Equipment, EquipmentHolder, EquipmentSet, EquipmentSetItem


class EquipmentItemInline(InlineFormSet):
    model = EquipmentItem
    form_class = EquipmentItemForm
    factory_kwargs = {'extra': 1}


class EquipmentSetInline(InlineFormSet):
    model = EquipmentSetItem
    form_class = EquipmentSetItemForm
    factory_kwargs = {'extra': 1}


class EquipmentHolderInline(InlineFormSet):
    model = EquipmentHolder
    form_class = EquipmentHolderUpdateForm
    factory_kwargs = {
        'min_num': 1,
        'max_num': 1,
        'extra': 0,
        'can_delete': False
    }


# Equipments

class EquipmentAdminListView(PaginationViewMixin,
                             ListView):
    model = Equipment
    ordering = ['name']


class EquipmentAdminDetailView(DetailView):
    model = Equipment


class EquipmentAdminCreateView(SuccessMessageMixin,
                               CreateView):
    model = Equipment
    fields = ['name', 'type', 'default']

    def get_success_message(self, cleaned_data):
        return "Successfully created equipment '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()


class EquipmentAdminUpdateView(SuccessMessageMixin,
                               UpdateView):
    model = Equipment
    fields = ['name', 'type', 'default']
    form = EquipmentUpdateForm

    def get_success_message(self, cleaned_data):
        return "Successfully updated equipment '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()


# Equipment sets

class EquipmentSetAdminListView(PaginationViewMixin,
                                ListView):
    model = EquipmentSet
    ordering = ['name']


class EquipmentSetAdminDetailView(DetailView):
    model = EquipmentSet


class EquipmentSetAdminCreateView(SuccessMessageWithInlinesMixin,
                                  UpdatedByWithInlinesMixin,
                                  CreateWithInlinesView):
    model = EquipmentSet
    inlines = [EquipmentSetInline]
    form_class = EquipmentSetCreateForm

    def get_success_message(self, cleaned_data):
        return "Successfully created equipment set '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()


class EquipmentSetAdminUpdateView(SuccessMessageWithInlinesMixin,
                                  UpdatedByWithInlinesMixin,
                                  UpdateWithInlinesView):
    model = EquipmentSet
    inlines = [EquipmentSetInline]
    form_class = EquipmentSetUpdateForm

    def get_success_message(self, cleaned_data):
        return "Successfully updated equipment set '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()


# Equipment holder

class EquipmentPermissionMixin(BasePermissionMixin):

    filter_field = 'id'
    profile_field = 'equipments'
    queryset = EquipmentHolder.objects.all()


class EquipmentHolderUpdateView(LoginRequiredMixin,
                                SuccessMessageWithInlinesMixin,
                                UpdatedByWithInlinesMixin,
                                EquipmentPermissionMixin,
                                UpdateWithInlinesView):
    model = EquipmentHolder
    inlines = [EquipmentItemInline]
    form_class = EquipmentHolderUpdateForm

    def get_success_message(self, cleaned_data):
        return "Successfully updated equipments"

    def get_success_url(self):
        return self.object.get_absolute_url()


# Equipment import and export

class EquipmentExportView(ExportModelMixin,
                          View):
    model = Equipment
    resource_class = EquipmentResource


class EquipmentImportView(ImportModelMixin,
                          TemplateView):
    model = Equipment
    resource_class = EquipmentResource

    process_import_url = 'equipment:process-import-equipment'
    import_breadcrumbs = {'equipment:list': _("Equipments")}


class EquipmentProcessImportView(SuccessMessageMixin,
                                 ProcessImportModelMixin,
                                 FormView):
    model = Equipment
    resource_class = EquipmentResource

    success_message = _('Successfully imported equipments')
    success_url = reverse_lazy('equipment:list')

    import_breadcrumbs = {'equipment:list': _("Equipments")}


class EquipmentSetExportView(ExportModelMixin,
                             View):
    model = EquipmentSet
    resource_class = EquipmentSetResource


class EquipmentSetImportView(ImportModelMixin,
                             TemplateView):
    model = EquipmentSet
    resource_class = EquipmentSetResource

    process_import_url = 'equipment:process-import-equipment-set'
    import_breadcrumbs = {'equipment:list-set': _("Equipment Sets")}


class EquipmentSetProcessImportView(SuccessMessageMixin,
                                    ProcessImportModelMixin,
                                    FormView):
    model = EquipmentSet
    resource_class = EquipmentSetResource

    success_message = _('Successfully imported equipment sets')
    success_url = reverse_lazy('equipment:list-set')

    import_breadcrumbs = {'equipment:list-set': _("Equipment Sets")}
