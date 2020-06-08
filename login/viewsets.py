import logging

from django.contrib.auth.models import User
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from emstrack.mixins import CreateModelUpdateByMixin, UpdateModelUpdateByMixin
from login.models import Client, ClientStatus
from login.permissions import IsUserOrAdminOrSuper
from .serializers import UserProfileSerializer, ClientSerializer, LoginTokenSerializer

logger = logging.getLogger(__name__)

# Django REST Framework Viewsets


# LoginToken view

class LoginTokenViewSet(mixins.RetrieveModelMixin):
    serializer_class = LoginTokenSerializer
    lookup_field = 'username'


# Profile viewset

class ProfileViewSet(viewsets.GenericViewSet):
   
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,
                          IsUserOrAdminOrSuper,)
    lookup_field = 'username'

    @action(detail=True, methods=['get'])
    def profile(self, request, **kwargs):
        """
        Retrieve user's extended profile.
        """
        return Response(UserProfileSerializer(self.get_object()).data)


# Client ViewSet

class ClientViewSet(CreateModelUpdateByMixin,
                    UpdateModelUpdateByMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    """
    API endpoint for manipulating Clients.

    list:
    Retrieve list of Client instances.

    create:
    Create or update Client instance.

    update:
    Update an existing Client instance.

    partial_update:
    Partially update existing Client instance.

    retrieve:
    Retrieve an existing Client instance.
    """

    permission_classes = (IsAuthenticated,)
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    lookup_field = 'client_id'
    update_by_field = 'user'

    def list(self, request, *args, **kwargs):
        # override list to restrict clients to online and reconnected only
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset.filter(status=ClientStatus.O.name) |\
                                        queryset.filter(status=ClientStatus.R.name))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
