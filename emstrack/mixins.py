import logging
import os
import tempfile

from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied

from import_export.forms import ImportForm, ConfirmImportForm
from import_export.resources import modelresource_factory

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

    # import / export formats
    formats = DEFAULT_FORMATS
    resource_class = None

    # import breadcrumbs
    import_breadcrumbs = {}

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
    #: template for import view
    template_name = 'import.html'
    process_import_url = 'process_import'

    def get_import_data_kwargs(self, request, *args, **kwargs):
        """
        Prepare kwargs for import_data.
        """
        form = kwargs.get('form')
        if form:
            kwargs.pop('form')
            return kwargs
        return {}

    def get(self, *args, **kwargs):
        return self.get_or_post(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.get_or_post(*args, **kwargs)

    def get_or_post(self, *args, **kwargs ):
        """
        Perform a dry_run of the import to make sure the import will not
        result in errors.  If there where no error, save the user
        uploaded file to a local temp file that will be used by
        'process_import' for the actual import.
        """
        context = self.get_context_data(**kwargs)

        import_formats = self.get_import_formats()
        form_kwargs = kwargs
        form = ImportForm(import_formats,
                          self.request.POST or None,
                          self.request.FILES or None,
                          **form_kwargs)

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
                logger.info(dataset)

                resource = self.get_import_resource_class()()
                imp_kwargs = self.get_import_data_kwargs(self.request, form=form, *args, **kwargs)
                result = resource.import_data(dataset, dry_run=True,
                                              raise_errors=False,
                                              user=self.request.user,
                                              **imp_kwargs)

            logger.info(result.__dict__)
            for row in result.rows:
                logger.info(row.__dict__)
            for row in result.invalid_rows:
                logger.info(row.__dict__)
            context['result'] = result

            if not result.has_errors() and not result.has_validation_errors():
                initial = {
                    'import_file_name': os.path.basename(uploaded_file.name),
                    'original_file_name': import_file.name,
                    'input_format': form.cleaned_data['input_format'],
                }
                context['confirm_form'] = ConfirmImportForm(initial=initial)

        else:
            resource = self.get_import_resource_class()()

        # set up context
        context['title'] = _("Import")
        context['form'] = form
        context['opts'] = self.model._meta
        context['fields'] = [f.column_name for f in resource.get_fields()]

        context['process_import_url'] = self.process_import_url
        context['import_breadcrumbs'] = self.import_breadcrumbs

        return super().render_to_response(context)


class ProcessImportModelMixin(BaseImportExportMixin):
    template_name = 'import.html'
    form_class = ConfirmImportForm

    def get_import_data_kwargs(self, request, *args, **kwargs):
        """
        Prepare kwargs for import_data.
        """
        form = kwargs.get('form')
        if form:
            kwargs.pop('form')
            return kwargs
        return {}

    def form_valid(self, form):

        import_formats = self.get_import_formats()
        input_format = import_formats[
            int(form.cleaned_data['input_format'])
        ]()
        import_file_name = os.path.join(
            tempfile.gettempdir(),
            form.cleaned_data['import_file_name']
        )

        # open import file
        with open(import_file_name, input_format.get_read_mode()) as import_file:

            # read file
            data = import_file.read()

            # handle encoding
            if not input_format.is_binary() and self.from_encoding:
                data = force_text(data, self.from_encoding)

            # create dataset
            dataset = input_format.create_dataset(data)
            logger.info(dataset)

            # import data, raise error if necessary
            resource = self.get_import_resource_class()()
            imp_kwargs = self.get_import_data_kwargs(self.request, form=form)
            result = resource.import_data(dataset, dry_run=False,
                                          raise_errors=True,
                                          user=self.request.user,
                                          **imp_kwargs)

        return super().form_valid(form)
