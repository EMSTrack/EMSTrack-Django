from django.shortcuts import render

from django.http import HttpResponse

from django.core.urlresolvers import reverse, reverse_lazy

from django.views import View
from django.views.generic import CreateView
from braces import views

# Create your views here.

from .models import Reporter, Ambulances
from .forms import AmbulanceCreateForm

class AmbulanceCreateView(CreateView):
	model = Ambulances
	form_class = AmbulanceCreateForm
	#context_object_name = "ambulances_form"
	success_url = reverse_lazy('ambulance_create')

class AmbulanceUpdateView(views.JSONResponseMixin, View):
    def update_ambulance(self, pk):
        # retrieve record
        record = Ambulances.objects.get(pk=pk)

        # lookup status
        status = self.request.GET.get('status')
        if status:
            # update record
            record.status = status

        # lookup location
        location = self.request.GET.get('location')
        if location:
            # update record
            record.location = location

        # save updated record
        record.save()
        return record

    def get(self, request, pk):
        record = self.update_ambulance(pk)
        return HttpResponse('Got it!')

    def get_ajax(self, request, pk):
        record = self.update_ambulance(pk)
        json = { 'status': record.status, 'location': record.location }
        return self.render_json_response(json)
     
class AmbulanceInfoView(views.JSONResponseMixin, View):
    def get_ajax(self, request, pk):
        s = Ambulances.objects.get(pk=pk)
        user = s.reporter.user
        
        json = {
            "status" : s.status,
            "reporter" : user.first_name + ' ' + user.last_name if s.reporter is not None else "No reporter"
        }
        return self.render_json_response(json)

    def get(self, request, pk):
        s = Ambulances.objects.get(pk=pk)
        user = s.reporter.user

        json = {
            "status" : s.status,
            "reporter" : user.first_name + ' ' + user.last_name if s.reporter is not None else "No reporter"
        }
        return self.render_json_response(json)