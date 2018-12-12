from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from extra_views import InlineFormSet, UpdateWithInlinesView

from emstrack.mixins import SuccessMessageWithInlinesMixin, UpdatedByWithInlinesMixin
from .models import EquipmentItem, Equipment, EquipmentHolder


class EquipmentItemInline(InlineFormSet):
    model = EquipmentItem
    fields = ['equipment', 'value', 'comment']
    factory_kwargs = {'extra': 1}


class EquipmentAdminListView(ListView):
    model = Equipment
    ordering = ['name']


class EquipmentAdminDetailView(DetailView):
    model = Equipment


class EquipmentAdminCreateView(SuccessMessageMixin,
                               CreateView):
    model = Equipment
    fields = ['name', 'type']

    def get_success_message(self, cleaned_data):
        return "Successfully created equipment '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()


class EquipmentAdminUpdateView(SuccessMessageMixin,
                               UpdateView):
    model = Equipment
    fields = ['name', 'type']

    def get_success_message(self, cleaned_data):
        return "Successfully updated equipment '{}'".format(self.object.name)

    def get_success_url(self):
        return self.object.get_absolute_url()


class EquipmentPermissionMixin(object):
    pass


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
