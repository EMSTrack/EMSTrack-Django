# Create your views here.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from braces import views
from django.views import View

from . import response_msg

from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
import json
import ast

from django.contrib.gis.geos import Point

from rest_framework import viewsets

from .models import Ambulances, TrackableDevice, Status
from .forms import AmbulanceUpdateForm, AmbulanceCreateForm, StatusCreateForm
from .serializers import AmbulancesSerializer, StatusSerializer, TrackableDeviceSerializer


class AmbulanceView(CreateView):
    model = Ambulances
    context_object_name = "ambulance_form"
    form_class = AmbulanceCreateForm
    success_url = reverse_lazy('ambulance_create')

    def get_context_data(self, **kwargs):
        context = super(AmbulanceView, self).get_context_data(**kwargs)
        context['ambulances'] = Ambulances.objects.all().order_by('license_plate')
        return context


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

    def get_context_data(self, **kwargs):
        context = super(StatusCreateView, self).get_context_data(**kwargs)
        context['statuses'] = Status.objects.all().order_by('status_string')
        return context

class AmbulanceUpdateView(views.JSONResponseMixin, View):

    def update_ambulance(self, pk):
        try:
            record = Ambulances.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return {
                "message": response_msg.NO_AMBULANCE_MSG["message"],
                "result": response_msg.NO_AMBULANCE_MSG["result"]
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
            "message": response_msg.AMBULANCE_UPDATE_SUCCESS["message"],
            "result": response_msg.AMBULANCE_UPDATE_SUCCESS["result"]
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
    template_name = 'ambulances/ambulance_map.html'

    def get_queryset(self):
        return Ambulances.objects.all()

    #def get(self, request):
        #return render(request, 'ambulances/ambulance_map.html')


class AmbulancesViewSet(viewsets.ModelViewSet):
    queryset = Ambulances.objects.all()
    serializer_class = AmbulancesSerializer

class StatusViewSet(viewsets.ModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
