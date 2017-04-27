from django.core.urlresolvers import reverse_lazy

from django.views.generic import ListView, CreateView
from braces import views
from django.views import View

from . import response_msg

from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
import ast

from django.contrib.gis.geos import Point

from rest_framework import viewsets
from rest_framework import filters
from rest_framework import mixins
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from .models import Ambulances, Status, Region, Call, Hospital
from .forms import AmbulanceCreateForm, StatusCreateForm
from .serializers import AmbulancesSerializer, StatusSerializer, RegionSerializer, CallSerializer, HospitalSerializer


class AmbulanceView(CreateView):
    model = Ambulances
    context_object_name = "ambulance_form"
    form_class = AmbulanceCreateForm
    success_url = reverse_lazy('ambulance_create')

    def get_context_data(self, **kwargs):
        context = super(AmbulanceView, self).get_context_data(**kwargs)
        context['ambulances'] = Ambulances.objects.all().order_by('license_plate')
        return context


class StatusCreateView(CreateView):
    model = Status
    context_object_name = "status_form"
    form_class = StatusCreateForm
    success_url = reverse_lazy("status_create")

    def get_context_data(self, **kwargs):
        context = super(StatusCreateView, self).get_context_data(**kwargs)
        context['statuses'] = Status.objects.all()
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


# Viewsets

# Custom viewset that only allows listing, retrieving, and updating
class ListRetrieveUpdateViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.UpdateModelMixin,
                                viewsets.GenericViewSet):
    pass


class AmbulancesViewSet(ListRetrieveUpdateViewSet):
    queryset = Ambulances.objects.all()
    serializer_class = AmbulancesSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('license_plate', 'status')


class StatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer


class CallViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Call.objects.all()
    serializer_class = CallSerializer


class HospitalViewSet(ListRetrieveUpdateViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'address')

class BaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Base.objects.all()
    serializer_class = BaseSerializer
