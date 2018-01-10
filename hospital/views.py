from django.urls import reverse_lazy
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, CreateView, UpdateView

import django_filters.rest_framework

from braces import views

from rest_framework import viewsets, filters, mixins, generics

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions
from rest_framework.decorators import detail_route

from .models import Hospital, HospitalEquipment

# Django views
                
