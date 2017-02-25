# Create your views here.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from braces import views
from django.views import View

from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
import json
import ast

from django.contrib.gis.geos import Point

from .models import Ambulances, TrackableDevice, Status
from .forms import AmbulanceUpdateForm, AmbulanceCreateForm, StatusCreateForm


class AmbulanceCreateView(CreateView):
    model = Ambulances
    context_object_name = "ambulance_form"
    form_class = AmbulanceCreateForm
    success_url = reverse_lazy('ambulance_create')


class AmbulanceInfoView(views.JSONResponseMixin, View):

    def build_json(self, request):

        idFilter = request.GET.get('id')
        statusFilter = request.GET.get('status')

        ambulances = Ambulances.objects.all()
        if (idFilter):
            ambulances = ambulances.filter(license_plate=idFilter)
        if (statusFilter):
            ambulances = ambulances.filter(status=statusFilter)

        json = []

        for ambulance in ambulances:
            json.append({
                "id": ambulance.license_plate,
                "status": ambulance.status,
                "lat": repr(ambulance.location.y),
                "long": repr(ambulance.location.x)
            })
        return json

    def get_ajax(self, request):
        json = self.build_json(request)
        return self.render_json_response(json)

    def get(self, request):
        json = self.build_json(request)
        return self.render_json_response(json)


class StatusCreateView(CreateView):
    model = Status
    context_object_name = "status_form"
    form_class = StatusCreateForm
    success_url = reverse_lazy("status_create")

class AmbulanceUpdateView(views.JSONResponseMixin, View):

    def update_ambulance(self, pk):
        try:
            record = Ambulances.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return {
                "message": "Found no ambulance with that license plate",
                "result": "failure"
            }

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
        return {
            "message": "Successful ambulance update",
            "result": "success"
        }

    def get_ajax(self, request, pk):
        record = self.update_ambulance(pk)

        json = {"status": record.status,
                "long": record.location.x,
                "lat": record.location.y
                }
        return self.render_json_response(json)

    # Through the browser, can render HTML for human-friendly viewing
    def get(self, request, pk):
        response = self.update_ambulance(pk)
        return self.render_json_response(response)

class CreateRoute(views.JSONResponseMixin, View):
    def post(self, request):
        # json_data = json.loads(request.body)
        points = ast.literal_eval(request.body)
        text = ""
        for p in points:
            text = text + p["alex"] + "\n"
        return HttpResponse(text)

class AmbulanceMap(views.JSONResponseMixin, views.AjaxResponseMixin, ListView):
    def get(self, request):
        return render(request, 'ambulances/ambulance_map.html')