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

# DRF Viewsets

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
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):

        #print('@perform_update')
        serializer.save(updated_by=self.request.user)

