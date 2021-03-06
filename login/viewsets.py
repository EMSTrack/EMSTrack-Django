import logging

from django.contrib.auth.models import User
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from emstrack.mixins import CreateModelUpdateByMixin, UpdateModelUpdateByMixin
from login.models import Client
from login.permissions import IsUserOrAdminOrSuper
from .serializers import UserProfileSerializer, ClientSerializer

logger = logging.getLogger(__name__)

# Django REST Framework Viewsets


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
