from django.http import HttpResponseRedirect

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

    def formset_valid(self, formset):

        self.object_list = formset.save(commit=False)
        for instance in self.object_list:
                            
            # add updated_by to formset instance
            instance.updated_by = self.request.user
            
            # then save
            instance.save()
        
        return HttpResponseRedirect(self.get_success_url())
    
class HospitalActionMixin:

    fields = [ 'name', 'location', 'comment' ]

    @property
    def success_message(self):
        return NotImplemented

    def form_valid(self, form):

        # add message
        messages.info(self.request, self.success_message)

        # add updated_by to form
        form.instance.updated_by = self.request.user
        
        # call super
        return super().form_valid(form)


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
    
