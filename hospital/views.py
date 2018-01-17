from django.http import HttpResponseRedirect

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from extra_views import InlineFormSet, CreateWithInlinesView, \
    UpdateWithInlinesView
from extra_views.generic import GenericInlineFormSet

from .models import Hospital, HospitalEquipment

from .forms import HospitalCreateForm, HospitalUpdateForm

from emstrack.mixins import BasePermissionMixin

# Django views

class HospitalPermissionMixin(BasePermissionMixin):

    filter_field = 'id'
    profile_field = 'hospitals'
    profile_values = 'hospital_id'
    queryset = Hospital.objects.all()
    
class HospitalActionMixin:

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

            # save but do not commit
            instances = formset.save(commit = False)
            
            # save form
            for obj in instances:
                
                # add updated_by to formset instance
                obj.updated_by = self.request.user
            
                # then save
                obj.save()
            
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
    form_class = HospitalCreateForm

    def get_success_url(self):
        return self.object.get_absolute_url()


class HospitalUpdateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         HospitalPermissionMixin,
                         UpdateWithInlinesView):
    model = Hospital
    inlines = [HospitalEquipmentInline]
    form_class = HospitalUpdateForm

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
    
