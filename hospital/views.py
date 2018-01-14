from django.http import HttpResponseRedirect

from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from extra_views import InlineFormSet, CreateWithInlinesView, \
    UpdateWithInlinesView
from extra_views.generic import GenericInlineFormSet

from .models import Hospital, HospitalEquipment

from .forms import HospitalEquipmentFormset

# Django views

class HospitalEquipmentInline(InlineFormSet):
    model = HospitalEquipment
    fields = ['equipment', 'value', 'comment']
    extra = 1
    
class HospitalActionMixin:

    fields = [ 'name', 'location', 'comment' ]

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
            
        return HttpResponseRedirect(reverse(self.get_success_url()))
    
class HospitalCreateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         CreateWithInlinesView):
    model = Hospital
    inlines = [HospitalEquipmentInline]
    success_url = 'hospital:detail'

    # def get_success_url(self):
    #     return self.object.get_absolute_url()


class HospitalUpdateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         UpdateWithInlinesView):
    model = Hospital
    inlines = [HospitalEquipmentInline]
    success_url = 'hospital:detail'

    # def get_success_url(self):
    #     return self.object.get_absolute_url()

class HospitalDetailView(LoginRequiredMixin,
                         DetailView):

    model = Hospital

class HospitalListView(LoginRequiredMixin,
                       ListView):

    model = Hospital
    
