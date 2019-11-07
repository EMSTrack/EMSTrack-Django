import logging

from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from import_export import resources, fields, widgets

# from emstrack.import_export import OneToOneField, DeferredSaveWidget

from login.models import GroupAmbulancePermission, GroupHospitalPermission, GroupProfile, UserProfile

logger = logging.getLogger(__name__)


class OneToOneField(fields.Field):

    def save(self, obj, data, is_m2m=False):
        logger.debug('> In OneToOneField save')
        super().save(obj, data, False)


class DeferredSaveWidget(widgets.ManyToManyWidget):
    """
    Widget that converts between representations of a ManyToMany relationships
    as a list and an actual ManyToMany field.
    :param model: The model the ManyToMany field refers to (required).
    :param separator: Defaults to ``','``.
    :param field: A field on the related model. Default is ``pk``.
    """

    def __init__(self, widget, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.widget = widget

    def clean(self, value, row=None, *args, **kwargs):
        logger.debug('> In DeferredSaveWidgdet clean')
        return self.widget.clean(value, row, *args, **kwargs)

    def render(self, value, obj=None):
        return self.widget.render(value, obj)


class UserResource(resources.ModelResource):
    is_dispatcher = OneToOneField(attribute='userprofile__is_dispatcher',
                                  widget=DeferredSaveWidget(widgets.BooleanWidget()),
                                  readonly=False)

    # is_dispatcher = OneToOneField(attribute='userprofile__is_dispatcher',
    #                               parent='userprofile',
    #                               child='id_dispatcher',
    #                               column_name='is_dispatcher',
    #                               widget=widgets.BooleanWidget(),
    #                               readonly=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_dispatcher', 'is_active')
        export_order = ('id', 'username', 'first_name', 'last_name', 'email',
                        'is_staff', 'is_dispatcher', 'is_active')

    # save userprofile related fields
    def after_save_instance(self, instance, using_transactions, dry_run):
        logger.info('instance')
        logger.info(instance.__dict__)
        if not using_transactions and dry_run:
            # we don't have transactions and we want to do a dry_run
            pass
        else:
            logger.info('instance.userprofile')
            logger.info(instance.userprofile.__dict__)
            instance.userprofile.save()


class GroupResource(resources.ModelResource):
    description = fields.Field(attribute='groupprofile__description',
                               widget=widgets.CharWidget(),
                               readonly=False)

    priority = fields.Field(attribute='groupprofile__priority',
                            widget=widgets.IntegerWidget(),
                            readonly=False)

    user_set = fields.Field(attribute='user_set',
                            widget=widgets.ManyToManyWidget(User, field='username', separator=','))

    class Meta:
        model = Group
        fields = ('id', 'name',
                  'description', 'priority', 'user_set')
        export_order = ('id', 'name',
                        'description', 'priority', 'user_set')

    # save userprofile related fields
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not using_transactions and dry_run:
            # we don't have transactions and we want to do a dry_run
            pass
        else:
            instance.groupprofile.save()


class GroupAmbulancePermissionResource(resources.ModelResource):
    group_name = fields.Field(attribute='group__name',
                              widget=widgets.CharWidget(),
                              readonly=True)

    ambulance_identifier = fields.Field(attribute='ambulance__identifier',
                                        widget=widgets.CharWidget(),
                                        readonly=True)

    class Meta:
        model = GroupAmbulancePermission
        fields = ('id', 'group_name', 'ambulance_identifier',
                  'can_read', 'can_write')
        export_order = ('id', 'group_name', 'ambulance_identifier',
                        'can_read', 'can_write')


class GroupHospitalPermissionResource(resources.ModelResource):
    group_name = fields.Field(attribute='group__name',
                              widget=widgets.CharWidget(),
                              readonly=True)

    hospital_name = fields.Field(attribute='hospital__name',
                                 widget=widgets.CharWidget(),
                                 readonly=True)

    class Meta:
        model = GroupHospitalPermission
        fields = ('id', 'group_name', 'hospital_name',
                  'can_read', 'can_write')
        export_order = ('id', 'group_name', 'hospital_name',
                        'can_read', 'can_write')
