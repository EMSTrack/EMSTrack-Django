from rest_framework import mixins

# CreateModelUpdateByMixin
from rest_framework.exceptions import PermissionDenied


class CreateModelUpdateByMixin(mixins.CreateModelMixin):

    def perform_create(self, serializer):
        
        serializer.save(updated_by=self.request.user)
    

# UpdateModelUpdateByMixin

class UpdateModelUpdateByMixin(mixins.UpdateModelMixin):

    def perform_update(self, serializer):
        
        serializer.save(updated_by=self.request.user)
        

# BasePermissionMixin
# TODO: Add group permissions

class BasePermissionMixin:

    filter_field = 'id'
    profile_field = 'ambulances'
    profile_values = 'ambulance_id'
    queryset = None
    
    def get_queryset(self):

        # print('@get_queryset {}({})'.format(self.request.user,
        #                                     self.request.method))
        
        # return all objects if superuser
        user = self.request.user
        if user.is_superuser:
            return super().get_queryset()

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

        # print('> user = {}, can_do = {}'.format(user, can_do))
        # print('> objects = {}'.format(Object.objects.all()))
        # print('> filtered objects = {}'.format(Object.objects.filter(id__in=can_do)))
        # add filter
        filter_params = {self.filter_field + '__in': can_do}

        # retrieve query
        return super().get_queryset().filter(**filter_params)