from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from braces import views

from .models import Hospital, HospitalEquipment

from .forms import HospitalEquipmentFormset

# Django views

class HospitalActionMixin:

    fields = [ 'name', 'location', 'comment' ]

    @property
    def success_message(self):
        return NotImplemented

    def form_valid(self, form):

        # add message
        messages.info(self.request, self.success_message)

        # handle formset
        formset = form['hospital_equipment_formset']
        if formset.is_valid():

            instances = formset.save(commit=False)
            for instance in instances:
                
                # add updated_by to formset instance
                instance.updated_by = self.request.user
                
                # then save
                instance.save()

            # add updated_by to form
            form.instance.updated_by = self.request.user
            
            # call form_valid
            return super().form_valid(form)
            
        else:

            # call form_invalid
            return super().form_invalid(form)
    
class HospitalCreateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         CreateView):

    model = Hospital
    success_message = 'Hospital created!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['hospital_equipment_formset'] = HospitalEquipmentFormset(self.request.POST)
        else:
            context['hospital_equipment_formset'] = HospitalEquipmentFormset()
        return context

class HospitalUpdateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         UpdateView):

    model = Hospital
    success_message = 'Hospital updated!'
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['hospital_equipment_formset'] = HospitalEquipmentFormset(self.request.POST,
                                                                             instance=self.object)
            context['hospital_equipment_formset'].full_clean()
        else:
            context['hospital_equipment_formset'] = HospitalEquipmentFormset(instance=self.object)
        return context

class HospitalDetailView(LoginRequiredMixin,
                         DetailView):

    model = Hospital

class HospitalListView(LoginRequiredMixin,
                       ListView):

    model = Hospital
    
