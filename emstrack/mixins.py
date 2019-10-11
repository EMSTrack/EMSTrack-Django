import logging
import os

from django.contrib import messages
from django.http import HttpResponseRedirect
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


# CreateModelUpdateByMixin

class CreateModelUpdateByMixin(mixins.CreateModelMixin):

    update_by_field = 'updated_by'

    def perform_create(self, serializer):
        serializer.save(**{self.update_by_field: self.request.user})


# UpdateModelUpdateByMixin

class UpdateModelUpdateByMixin(mixins.UpdateModelMixin):

    update_by_field = 'updated_by'

    def perform_update(self, serializer):
        serializer.save(**{self.update_by_field: self.request.user})


# BasePermissionMixin

class BasePermissionMixin:
    filter_field = 'id'
    profile_field = 'ambulances'
    queryset = None
    dispatcher_override = False

    def get_queryset(self):

        # print('@get_queryset {}({})'.format(self.request.user,
        #                                     self.request.method))

        # return all objects if superuser
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return super().get_queryset()

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        # get permissions
        from login.permissions import get_permissions
        permissions = get_permissions(user)

        # otherwise only return objects that the user can read or write to
        # if dispatcher_override is True substitute read permissions for write permissions
        if self.request.method == 'GET' or (self.dispatcher_override and user.userprofile.is_dispatcher):
            # objects that the user can read
            can_do = permissions.get_can_read(self.profile_field)

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            # objects that the user can write to
            can_do = permissions.get_can_write(self.profile_field)

        else:
            raise PermissionDenied()

        # add filter
        filter_params = {self.filter_field + '__in': can_do}

        logger.debug('can_do = {}'.format(can_do))
        logger.debug('filter_params = {}'.format(filter_params))

        # retrieve query
        return super().get_queryset().filter(**filter_params)


class SuccessMessageWithInlinesMixin:

    def get_success_message(self, cleaned_data):
        return NotImplemented

    def forms_valid(self, form, inlines):

        # add message
        messages.info(self.request, self.get_success_message(form.cleaned_data))

        # call super
        return super().forms_valid(form, inlines)


class UpdatedByWithInlinesMixin:

    def forms_valid(self, form, inlines):

        # add updated_by to form and save
        form.instance.updated_by = self.request.user
        self.object = form.save()

        # save formsets
        for formset in inlines:

            # save but do not commit
            instances = formset.save(commit=False)

            # save form
            for obj in instances:
                # add updated_by to formset instance
                obj.updated_by = self.request.user

                # then save
                obj.save()

        return HttpResponseRedirect(self.get_success_url())


class UpdatedByMixin:

    def form_valid(self, form):
        # add updated_by to form and save
        form.instance.updated_by = self.request.user

        # call super
        return super().form_valid(form)


class PublishMixin:

    def save(self, *args, **kwargs):

        # publish?
        publish = kwargs.pop('publish', True)

        # save to Call
        super().save(*args, **kwargs)

        if publish and os.environ.get("DJANGO_ENABLE_MQTT_PUBLISH", "True"):
            self.publish()
