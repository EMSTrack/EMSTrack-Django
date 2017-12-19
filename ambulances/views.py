import django_filters.rest_framework
#from django.core.urlresolvers import reverse_lazy
from django.urls import reverse_lazy
from django.http import Http404
from django.shortcuts import get_object_or_404

from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, CreateView, UpdateView
from braces import views

from rest_framework import viewsets
from rest_framework import filters
from rest_framework import mixins
from rest_framework import generics

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions
from rest_framework.decorators import detail_route

from .models import Ambulance, Call, Hospital, \
    EquipmentCount, Base, AmbulanceRoute, \
    Profile

from .forms import AmbulanceCreateForm, AmbulanceUpdateForm

from .serializers import ProfileSerializer, AmbulanceSerializer

# Django REST Viewsets

class IsUserOrAdminOrSuper(permissions.BasePermission):
    """
    Only user or staff can see or modify
    """

    def has_object_permission(self, request, view, obj):
        return (request.user.is_superuser or
                request.user.is_staff or
                obj.user == request.user)

# Profile viewset

class ProfileViewSet(mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,
                          IsUserOrAdminOrSuper,)

# Ambulance viewset

class AmbulanceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):

    #queryset = Ambulance.objects.all()
    serializer_class = AmbulanceSerializer

    def get_queryset(self):

        #print('@get_queryset {}({})'.format(self.request.user,
        #                                    self.request.method))
        
        # return all ambulance if superuser
        user = self.request.user
        if user.is_superuser:
            return Ambulance.objects.all()

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        # print('> METHOD = {}'.format(self.request.method))
        # otherwise only return ambulances that the user can read or write to
        if self.request.method == 'GET':
            # ambulances that the user can read
            can_do = user.profile.ambulances.filter(can_read=True)

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            # ambulances that the user can write to
            can_do = user.profile.ambulances.filter(can_write=True)
            
        else:
            raise PermissionDenied()

        #print('user = {}, can_do = {}'.format(user, can_do))
        return Ambulance.objects.filter(id__in=can_do)

    
    def perform_create(self, serializer):
        
        #print('@perform_create')
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        
        serializer.save(updated_by=self.request.user)
        

    def perform_update(self, serializer):

        #print('@perform_update')
        serializer.save(updated_by=user)

# Django views
                
# Ambulance list page
class AmbulanceListView(ListView):
    model = Ambulance
    template_name = 'ambulances/ambulance_list.html'
    context_object_name = "ambulances"

# Ambulance list page
class AmbulanceView(CreateView):
    model = Ambulance
    context_object_name = "ambulance_form"
    form_class = AmbulanceCreateForm
    success_url = reverse_lazy('ambulance')

    def get_context_data(self, **kwargs):
        context = super(AmbulanceView, self).get_context_data(**kwargs)
        context['ambulances'] = Ambulance.objects.all().order_by('id')
        return context

# Ambulance update page
class AmbulanceUpdateView(UpdateView):
    model = Ambulance
    form_class = AmbulanceUpdateForm
    template_name = 'ambulances/ambulance_edit.html'
    success_url = reverse_lazy('ambulance')

    def get_object(self, queryset=None):
        obj = Ambulance.objects.get(id=self.kwargs['pk'])
        return obj

    def get_context_data(self, **kwargs):
        context = super(AmbulanceUpdateView, self).get_context_data(**kwargs)
        context['identifier'] = self.kwargs['pk']
        return context

# Call list page
class CallView(ListView):
    model = Call
    template_name = 'ambulances/dispatch_list.html'
    context_object_name = "ambulance_call"

# Admin page
class AdminView(ListView):
    model = Call
    template_name = 'ambulances/dispatch_list.html'
    context_object_name = "ambulance_call"
    
# # AmbulanceStatus list page
# class AmbulanceStatusCreateView(CreateView):
#     model = AmbulanceStatus
#     context_object_name = "ambulance_status_form"
#     form_class = AmbulanceStatusCreateForm
#     success_url = reverse_lazy('status')

#     def get_context_data(self, **kwargs):
#         context = super(AmbulanceStatusCreateView, self).get_context_data(**kwargs)
#         context['statuses'] = AmbulanceStatus.objects.all().order_by('id')
#         return context


# # AmbulanceStatus update page
# class AmbulanceStatusUpdateView(UpdateView):
#     model = AmbulanceStatus
#     form_class = AmbulanceStatusUpdateForm
#     template_name = 'ambulances/ambulance_status_edit.html'
#     success_url = reverse_lazy('status')

#     def get_object(self, queryset=None):
#         obj = AmbulanceStatus.objects.get(id=self.kwargs['pk'])
#         return obj

#     def get_context_data(self, **kwargs):
#         context = super(AmbulanceStatusUpdateView, self).get_context_data(**kwargs)
#         context['id'] = self.kwargs['pk']
#         return context


# Ambulance map page
class AmbulanceMap(views.JSONResponseMixin, views.AjaxResponseMixin, ListView):
    template_name = 'ambulances/ambulance_map.html'

    def get_queryset(self):
        return Ambulance.objects.all()


        
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


# Defines viewsets
# Viewsets combine different request types (GET, PUSH, etc.) in a single view class
# class AmbulanceViewSet(ListRetrieveUpdateViewSet):

#     # Specify model to expose
#     queryset = Ambulance.objects.all()

#     # Specify the serializer to package the data in JSON
#     serializer_class = AmbulanceSerializer

#     # Specify django REST's filtering system
#     filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)

#     # Specify fields that user can filter GET by
#     filter_fields = ('identifier', 'status')


# class AmbulanceStatusViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = AmbulanceStatus.objects.all()
#     serializer_class = AmbulanceStatusSerializer


# class CallViewSet(ListCreateViewSet):
#     queryset = Call.objects.all()
#     serializer_class = CallSerializer


# class EquipmentCountViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
#     queryset = EquipmentCount.objects.all()
#     serializer_class = EquipmentCountSerializer


# class HospitalViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Hospital.objects.all()
#     serializer_class = HospitalSerializer
#     filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
#     filter_fields = ('name', 'address')


# class BaseViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Base.objects.all()
#     serializer_class = BaseSerializer


# class AmbulanceRouteViewSet(ListCreateViewSet):
#     queryset = AmbulanceRoute.objects.all()
#     serializer_class = AmbulanceRouteSerializer
