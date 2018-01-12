from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from braces import views

from .models import Hospital, HospitalEquipment

# Django views

class HospitalActionMixin:

    fields = [ ]

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

class HospitalUpdateView(LoginRequiredMixin,
                         HospitalActionMixin,
                         UpdateView):

    model = Hospital
    success_message = 'Hospital updated!'

class HospitalDetailView(LoginRequiredMixin,
                         DetailView):

    model = Hospital

class HospitalListView(LoginRequiredMixin,
                       ListView):

    model = Hospital
    
