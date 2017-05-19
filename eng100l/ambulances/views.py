from django.core.urlresolvers import reverse_lazy

from django.views.generic import ListView, CreateView, UpdateView
from braces import views

from rest_framework import viewsets
from rest_framework import filters
from rest_framework import mixins

from .models import Ambulances, Status, Region, Call, Hospital, EquipmentCount, Base, Route
from .forms import AmbulanceCreateForm, AmbulanceUpdateForm, StatusCreateForm, StatusUpdateForm, CallCreateForm
from .serializers import AmbulancesSerializer, StatusSerializer, RegionSerializer, CallSerializer, HospitalSerializer, EquipmentCountSerializer, RouteSerializer, BaseSerializer


class AmbulanceView(CreateView):
    model = Ambulances
    context_object_name = "ambulance_form"
    form_class = AmbulanceCreateForm
    success_url = reverse_lazy('ambulance')

    def get_context_data(self, **kwargs):
        context = super(AmbulanceView, self).get_context_data(**kwargs)
        #context['ambulances'] = Ambulances.objects.all().extra(select={'order': "CAST(license_plate as INTEGER)"}).order_by('order')
        context['ambulances'] = Ambulances.objects.all().order_by('id')
        return context


class AmbulanceUpdateView(UpdateView):
    model = Ambulances
    form_class = AmbulanceUpdateForm
    template_name = 'ambulances/ambulance_edit.html'
    success_url = reverse_lazy('ambulance')

    def get_object(self, queryset=None):
        obj = Ambulances.objects.get(id=self.kwargs['pk'])
        return obj

    def get_context_data(self, **kwargs):
        context = super(AmbulanceUpdateView, self).get_context_data(**kwargs)
        context['license_plate'] = self.kwargs['license_plate']
        return context


class CallView(ListView):
    model = Call
    template_name = 'ambulances/dispatch_list.html'
    context_object_name = "ambulance_call"


class StatusCreateView(CreateView):
    model = Status
    context_object_name = "status_form"
    form_class = StatusCreateForm
    success_url = reverse_lazy('status')

    def get_context_data(self, **kwargs):
        context = super(StatusCreateView, self).get_context_data(**kwargs)
        context['statuses'] = Status.objects.all().order_by('id')
        return context


class StatusUpdateView(UpdateView):
    model = Status
    form_class = StatusUpdateForm
    template_name = 'ambulances/status_edit.html'
    success_url = reverse_lazy('status')

    def get_object(self, queryset=None):
        obj = Status.objects.get(id=self.kwargs['pk'])
        return obj

    def get_context_data(self, **kwargs):
        context = super(StatusUpdateView, self).get_context_data(**kwargs)
        context['id'] = self.kwargs['pk']
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


class CallViewSet(ListCreateViewSet):
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


class BaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Base.objects.all()
    serializer_class = BaseSerializer


class RouteViewSet(ListCreateViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
