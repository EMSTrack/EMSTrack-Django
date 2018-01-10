from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, mixins, generics, filters, permissions
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Ambulance

from .serializers import AmbulanceSerializer

# Django REST Framework Viewsets

# CreateModelUpdateByMixin

class CreateModelUpdateByMixin(mixins.CreateModelMixin):

    def perform_create(self, serializer):
        
        serializer.save(updated_by=self.request.user)
    
# UpdateModelUpdateByMixin

class UpdateModelUpdateByMixin(mixins.UpdateModelMixin):

    def perform_update(self, serializer):
        
        serializer.save(updated_by=self.request.user)

# BasePermissionViewSet

class BasePermissionViewSet(viewsets.GenericViewSet):

    filter_field = 'id'
    profile_field = 'ambulances'
    profile_values = 'ambulance_id'
    queryset = None
    
    def get_queryset(self):

        #print('@get_queryset {}({})'.format(self.request.user,
        #                                    self.request.method))
        
        # return all objects if superuser
        user = self.request.user
        if user.is_superuser:
            return self.queryset

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        # print('> METHOD = {}'.format(self.request.method))
        # otherwise only return objects that the user can read or write to
        if self.request.method == 'GET':
            # objects that the user can read
            can_do = getattr(user.profile,
                             self.profile_field).filter(can_read=True).values(self.profile_values)

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            # objects that the user can write to
            can_do = getattr(user.profile,
                             self.profile_field).filter(can_write=True).values(self.profile_values)
            
        else:
            raise PermissionDenied()

        #print('> user = {}, can_do = {}'.format(user, can_do))
        #print('> objects = {}'.format(Object.objects.all()))
        #print('> filtered objects = {}'.format(Object.objects.filter(id__in=can_do)))
        filter = {}
        filter[self.filter_field + '__in'] = can_do
        return self.queryset.filter(**filter)
    

# AmbulancePermission

class AmbulancePermissionViewSet(BasePermissionViewSet):

    filter_field = 'id'
    profile_field = 'ambulances'
    profile_values = 'ambulance_id'
    queryset = Ambulance.objects.all()
    
# Ambulance viewset

class AmbulanceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       CreateModelUpdateByMixin,
                       UpdateModelUpdateByMixin,
                       AmbulancePermissionViewSet):

    serializer_class = AmbulanceSerializer

