import logging
import os
import tempfile

from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.encoding import force_text
from import_export.forms import ImportForm, ConfirmImportForm
from import_export.resources import modelresource_factory
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied

from import_export.formats.base_formats import DEFAULT_FORMATS

from environs import Env

env = Env()
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

        if publish and env.bool("DJANGO_ENABLE_MQTT_PUBLISH", default=True):
            self.publish()


# ImportExport mixin
# https://stackoverflow.com/questions/24008820/use-django-import-export-with-class-based-views

# BaseImportExportMixin
class BaseImportExportMixin:
    model = None
    from_encoding = "utf-8"

    #: import / export formats
    formats = DEFAULT_FORMATS
    #: template for import view
    import_template_name = 'import.html'
    resource_class = None

    def get_import_formats(self):
        """
        Returns available import formats.
        """
        return [f for f in self.formats if f().can_import()]

    def get_resource_class(self):
        if not self.resource_class:
            return modelresource_factory(self.model)
        else:
            return self.resource_class

    def get_import_resource_class(self):
        """
        Returns ResourceClass to use for import.
        """
        return self.get_resource_class()

    def get_export_resource_class(self):
        """
        Returns ResourceClass to use for import.
        """
        return self.get_resource_class()


# Export Mixin
class ExportModelMixin(BaseImportExportMixin):
    filename = 'export.csv'

    def get(self, *args, **kwargs ):
        resource = self.get_export_resource_class()()
        dataset = resource.export()
        response = HttpResponse(dataset.csv, content_type="csv")
        response['Content-Disposition'] = 'attachment; filename={}'.format(self.filename)
        return response


# ImportModelMixin
class ImportModelMixin(BaseImportExportMixin):
    process_import_url = 'process_import'

    def get(self, *args, **kwargs ):
        """
        Perform a dry_run of the import to make sure the import will not
        result in errors.  If there where no error, save the user
        uploaded file to a local temp file that will be used by
        'process_import' for the actual import.
        """
        resource = self.get_import_resource_class()()

        context = {}

        import_formats = self.get_import_formats()
        form = ImportForm(import_formats,
                          self.request.POST or None,
                          self.request.FILES or None)

        if self.request.POST and form.is_valid():
            input_format = import_formats[
                int(form.cleaned_data['input_format'])
            ]()
            import_file = form.cleaned_data['import_file']
            # first always write the uploaded file to disk as it may be a
            # memory file or else based on settings upload handlers
            with tempfile.NamedTemporaryFile(delete=False) as uploaded_file:
                for chunk in import_file.chunks():
                    uploaded_file.write(chunk)

            # then read the file, using the proper format-specific mode
            with open(uploaded_file.name,
                      input_format.get_read_mode()) as uploaded_import_file:
                # warning, big files may exceed memory
                data = uploaded_import_file.read()
                if not input_format.is_binary() and self.from_encoding:
                    data = force_text(data, self.from_encoding)
                dataset = input_format.create_dataset(data)
                result = resource.import_data(dataset, dry_run=True,
                                              raise_errors=False)

            context['result'] = result

            if not result.has_errors():
                context['confirm_form'] = ConfirmImportForm(initial={
                    'import_file_name': os.path.basename(uploaded_file.name),
                    'input_format': form.cleaned_data['input_format'],
                })

        context['form'] = form
        context['opts'] = self.model._meta
        context['fields'] = [f.column_name for f in resource.get_fields()]
        context['process_import_url'] = self.process_import_url

        return TemplateResponse(self.request, [self.import_template_name], context)

    def post(self, *args, **kwargs ):
        """
        Perform a dry_run of the import to make sure the import will not
        result in errors.  If there where no error, save the user
        uploaded file to a local temp file that will be used by
        'process_import' for the actual import.
        """
        resource = self.get_import_resource_class()()

        context = {}

        import_formats = self.get_import_formats()
        form = ImportForm(import_formats,
                          self.request.POST or None,
                          self.request.FILES or None)

        if self.request.POST and form.is_valid():
            input_format = import_formats[
                int(form.cleaned_data['input_format'])
            ]()
            import_file = form.cleaned_data['import_file']
            # first always write the uploaded file to disk as it may be a
            # memory file or else based on settings upload handlers
            with tempfile.NamedTemporaryFile(delete=False) as uploaded_file:
                for chunk in import_file.chunks():
                    uploaded_file.write(chunk)

            # then read the file, using the proper format-specific mode
            with open(uploaded_file.name,
                      input_format.get_read_mode()) as uploaded_import_file:
                # warning, big files may exceed memory
                data = uploaded_import_file.read()
                if not input_format.is_binary() and self.from_encoding:
                    data = force_text(data, self.from_encoding)
                dataset = input_format.create_dataset(data)
                result = resource.import_data(dataset, dry_run=True,
                                              raise_errors=False)

            context['result'] = result

            if not result.has_errors():
                context['confirm_form'] = ConfirmImportForm(initial={
                    'import_file_name': os.path.basename(uploaded_file.name),
                    'input_format': form.cleaned_data['input_format'],
                })

        context['form'] = form
        context['opts'] = self.model._meta
        context['fields'] = [f.column_name for f in resource.get_fields()]
        context['process_import_url'] = self.process_import_url

        return TemplateResponse(self.request, [self.import_template_name], context)


class ProcessImportModelMixin(BaseImportExportMixin):

    def post(self, *args, **kwargs ):
        """
        Perform the actual import action (after the user has confirmed he/she wishes to import)
        """
        opts = self.model._meta
        resource = self.get_import_resource_class()()

        confirm_form = ConfirmImportForm(self.request.POST)
        if confirm_form.is_valid():
            import_formats = self.get_import_formats()
            input_format = import_formats[
                int(confirm_form.cleaned_data['input_format'])
            ]()
            import_file_name = os.path.join(
                tempfile.gettempdir(),
                confirm_form.cleaned_data['import_file_name']
            )
            import_file = open(import_file_name, input_format.get_read_mode())
            data = import_file.read()
            if not input_format.is_binary() and self.from_encoding:
                data = force_text(data, self.from_encoding)
            dataset = input_format.create_dataset(data)

            result = resource.import_data(dataset, dry_run=False,
                                          raise_errors=True)

            success_message = _('Import finished')
            messages.success(self.request, success_message)
            import_file.close()

            url = reverse('%s_list' % (str(opts.app_label).lower()))
            return HttpResponseRedirect(url)
