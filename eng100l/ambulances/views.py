from django.core.urlresolvers import reverse_lazy

from django.views.generic import ListView, CreateView
from braces import views
from django.views import View

from . import response_msg

from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
import ast

from rest_framework import viewsets
from rest_framework import filters
from rest_framework import mixins
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from .models import Ambulances, Status, Region, Call, Hospital, EquipmentCount, Route
from .forms import AmbulanceCreateForm, StatusCreateForm, AmbulanceEditForm
from .serializers import AmbulancesSerializer, StatusSerializer, RegionSerializer, CallSerializer, HospitalSerializer, EquipmentCountSerializer, RouteSerializer


class AmbulanceView(CreateView):
    model = Ambulances
    context_object_name = "ambulance_form"
    form_class = AmbulanceCreateForm
    success_url = reverse_lazy('ambulance')

    def get_context_data(self, **kwargs):
        context = super(AmbulanceView, self).get_context_data(**kwargs)
        context['ambulances'] = Ambulances.objects.all().order_by('license_plate')
        return context


def ambulance_edit(request, pk):
    ambulance = get_object_or_404(Ambulances, pk=pk)
    if request.method == "POST":
        form = AmbulanceEditForm(request.POST, instance=ambulance)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('ambulance')
    else:
        form = AmbulanceEditForm(instance=ambulance)
    return render(request, 'ambulances/ambulance_edit.html', {'form': form})


class StatusCreateView(CreateView):
    model = Status
    context_object_name = "status_form"
    form_class = StatusCreateForm
    success_url = reverse_lazy("status")

    def get_context_data(self, **kwargs):
        context = super(StatusCreateView, self).get_context_data(**kwargs)
        context['statuses'] = Status.objects.all()
        return context


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

class ListCreateViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin,
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

class EquipmentCountViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = EquipmentCount.objects.all()
    serializer_class = EquipmentCountSerializer

class HospitalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'address')

class RouteViewSet(ListCreateViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
