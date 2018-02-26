from django.contrib.auth.models import User

from rest_framework import viewsets, mixins, generics, filters, permissions
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Profile

from .serializers import ExtendedProfileSerializer

# Django REST Framework Viewsets


class IsUserOrAdminOrSuper(permissions.BasePermission):
    """
    Only user or staff can see or modify
    """

    def has_object_permission(self, request, view, obj):
        return (request.user.is_superuser or
                request.user.is_staff or
                obj == request.user)


# Profile viewset

class ProfileViewSet(viewsets.GenericViewSet):
   
    queryset = User.objects.all()
    serializer_class = ExtendedProfileSerializer
    permission_classes = (permissions.IsAuthenticated,
                          IsUserOrAdminOrSuper,)
    lookup_field = 'username'

    @detail_route(methods=['get'])
    def profile(self, request, **kwargs):
        """
        Retrieve user's extended profile.
        """
        return Response(ExtendedProfileSerializer(self.get_object()).data)

