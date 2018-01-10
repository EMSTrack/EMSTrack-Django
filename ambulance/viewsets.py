from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, mixins, generics, filters, permissions
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from util.mixins import CreateModelUpdateByMixin, UpdateModelUpdateByMixin
from util.viewsets import BasePermissionViewSet

from .models import Ambulance

from .serializers import AmbulanceSerializer

# Django REST Framework Viewsets

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

