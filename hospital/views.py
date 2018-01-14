from django.http import HttpResponseRedirect

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from extra_views import InlineFormSet, CreateWithInlinesView, \
    UpdateWithInlinesView
from extra_views.generic import GenericInlineFormSet

from .models import Hospital, HospitalEquipment

from .forms import HospitalEquipmentFormset

from util.mixins import BasePermissionMixin

# Django views

class HospitalPermissionMixin(BasePermissionMixin):

    filter_field = 'id'
    profile_field = 'hospitals'
    profile_values = 'hospital_id'
    queryset = Hospital.objects.all()
    
class HospitalActionMixin:

    fields = [ 'name',
               'number', 'street', 'unit',
               'city', 'state', 'zipcode', 'country',
               'location', 'comment' ]

    @property
    def success_message(self):
        return NotImplemented

    def forms_valid(self, form, inlines):

        # add message
        messages.info(self.request, self.success_message)

        # add updated_by to form and save
        form.instance.updated_by = self.request.user
        self.object = form.save()

        # save formsets
        for formset in inlines:

            # add updated_by to formset instance
            formset.updated_by = self.request.user
            
            # then save
            formset.save()
            
        return HttpResponseRedirect(self.get_success_url())
    
class HospitalEquipmentInline(InlineFormSet):

    model = HospitalEquipment
    fields = ['equipment', 'value', 'comment']
    extra = 1
    
class HospitalCreateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         HospitalPermissionMixin,
                         CreateWithInlinesView):
    model = Hospital
    inlines = [HospitalEquipmentInline]
    success_url = 'hospital:detail'

    def get_success_url(self):
        return self.object.get_absolute_url()


class HospitalUpdateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         HospitalPermissionMixin,
                         UpdateWithInlinesView):
    model = Hospital
    inlines = [HospitalEquipmentInline]

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
    
