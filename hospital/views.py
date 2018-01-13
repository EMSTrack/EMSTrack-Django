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
        messages.info(self.request, self.success_message)
        return super().form_valid(form)
    
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

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['hospital_equipment_formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
class HospitalUpdateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         UpdateView):

    model = Hospital
    success_message = 'Hospital updated!'
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['hospital_equipment_formset'] = HospitalEquipmentFormset(self.request.POST, instance=self.object)
            context['hospital_equipment_formset'].full_clean()
        else:
            context['hospital_equipment_formset'] = HospitalEquipmentFormset(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['hospital_equipment_formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))
        
class HospitalDetailView(LoginRequiredMixin,
                         DetailView):

    model = Hospital

class HospitalListView(LoginRequiredMixin,
                       ListView):

    model = Hospital
    
