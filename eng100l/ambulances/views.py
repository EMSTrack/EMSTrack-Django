# Create your views here.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from braces import views
from django.views import View

from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader

from django.contrib.gis.geos import Point

from .models import AED, Ambulances, Reporter
from .forms import AEDUpdateForm, AEDCreateForm, AmbulanceUpdateForm, AmbulanceCreateForm, ReporterCreateForm

class AmbulanceCreateView(CreateView):
    model = Ambulances
    context_object_name = "ambulance_form"
    form_class = AmbulanceCreateForm
    success_url = reverse_lazy('list')

class AmbulanceInfoView(views.JSONResponseMixin, View):
    def build_json(self, pk):
    	record = Ambulances.objects.get(pk=pk)
    	json = {
    		"status" : record.status,
    		"reporter" : record.reporter if record.reporter else "No Reporter",
    		"location" : "(" + repr(record.location.x) + "," 
    						 + repr(record.location.y) + ")"
    	}
    	return json

    def get_ajax(self, request, pk):
        json = self.build_json(pk)
        return self.render_json_response(json)

    def get(self, request, pk):
        json = self.build_json(pk)
        return self.render_json_response(json)

class AmbulanceUpdateView(views.JSONResponseMixin, View):
    def update_ambulance(self, pk):
        record = Ambulances.objects.get(pk=pk)

        # lookup status
        status = self.request.GET.get('status')
        if status:
            # update record
            record.status = status

        # lookup location
        longitude = float(self.request.GET.get('long'))
        latitude = float(self.request.GET.get('lat'))
        if longitude and latitude:
            # update record
            location = Point(longitude, latitude, srid=4326)
            record.location = location

        # save updated record
        record.save()
        return record

    def get_ajax(self, request, pk):
        record = self.update_ambulance(pk)
        #return HttpResponse('Got it!')

        json = { "status" : record.status,
                 "long" : record.location.x,
                 "lat" : record.location.y 
                }
        return self.render_json_response(json)

    #Through the browser, can render HTML for human-friendly viewing
    def get(self, request, pk):
        record = self.update_ambulance(pk)
        return HttpResponse('Got it!')


class ReporterCreateView(CreateView):
    model = Reporter
    context_object_name = "reporter_form"
    form_class = ReporterCreateForm
    success_url = reverse_lazy('list')

class AmbulanceView(views.JSONResponseMixin, views.AjaxResponseMixin, ListView):
    model = Ambulances
    context_object_name = 'ambulances_list'

    def get_ajax(self, request, *args, **kwargs):
        json = []
        entries = self.get_queryset()
        for entry in entries:
            json.append({
                'type': 'Ambulances',
                'location': { 'x': entry.location.x,
                              'y': entry.location.y },
                'license_plate': entry.license_plate,
                'status': entry.status,
            })
        return self.render_json_response(json)

    def index(request):
        ambulances = Ambulances.objects.all()
        len(ambulances)
        return render(request, 'craed/ambulances_list.html', {'ambulances_list': ambulances})

    def lat(self):
        return float(self.request.GET.get('lat') or 32.52174913333495)

    def lng(self):
        return float(self.request.GET.get('lng') or -117.0096155300208)


