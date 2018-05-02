from django.contrib.auth.models import User

from rest_framework import viewsets, mixins, generics, filters, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from .models import UserProfile

from .serializers import UserProfileSerializer

# Django REST Framework Viewsets


class IsUserOrAdminOrSuper(permissions.BasePermission):
    """
    Only user or staff can see or modify
    """

    def has_object_permission(self, request, view, obj):
        return (request.user.is_superuser or
                request.user.is_staff or
                obj == request.user)


class IsCreateByAdminOrSuper(permissions.BasePermission):
    """
    Only user or staff can create
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_staff or request.user.is_superuser
        else:
            return True


# Profile viewset

class ProfileViewSet(viewsets.GenericViewSet):
   
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,
                          IsUserOrAdminOrSuper,)
    lookup_field = 'username'

    @detail_route(methods=['get'])
    def profile(self, request, **kwargs):
        """
        Retrieve user's extended profile.
        """
        return Response(UserProfileSerializer(self.get_object()).data)

