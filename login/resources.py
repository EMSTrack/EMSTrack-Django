import logging

from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from import_export import resources, fields, widgets

from login.models import GroupAmbulancePermission, GroupHospitalPermission
from login.util import PasswordReset

logger = logging.getLogger(__name__)


class UserResource(resources.ModelResource):
    is_dispatcher = fields.Field(attribute='userprofile__is_dispatcher',
                                 widget=widgets.PostSaveWidget(widgets.BooleanWidget()),
                                 readonly=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_dispatcher', 'is_active')
        export_order = ('id', 'username', 'first_name', 'last_name', 'email',
                        'is_staff', 'is_dispatcher', 'is_active')

    # save userprofile related fields
    def after_post_save_instance(self, instance, row, using_transactions, dry_run):
        instance.userprofile.save()


class UserImportResource(UserResource):
    reset_password = fields.Field(column_name='reset_password',
                                  widget=widgets.BooleanWidget(),
                                  readonly=False)

    def __init__(self):
        super().__init__()
        self.is_new = False
        self.request = None
        self.reset_password = False

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_dispatcher', 'is_active', 'reset_password')
        export_order = ('id', 'username', 'first_name', 'last_name', 'email',
                        'is_staff', 'is_dispatcher', 'is_active', 'reset_password')

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        self.request = kwargs.get('request', None)

    def before_save_instance(self, instance, using_transactions, dry_run):
        self.is_new = not instance.id

    def after_post_save_instance(self, instance, row, using_transactions, dry_run):

        # save userprofile related fields
        super().after_post_save_instance(instance, row, using_transactions, dry_run)

        # reset_password
        self.reset_password = self.fields['reset_password'].clean(row)

        # is new?
        if self.reset_password is None:
            self.reset_password = self.is_new

        if self.reset_password and not dry_run:
            # reset password
            PasswordReset(instance.email, self.request).send_reset()

    def after_import_row(self, row, row_result, **kwargs):
        logger.info('after_import_row')
        row_result.diff[8] = '{}'.format(1 if self.reset_password else 0)
        logger.info(row)
        logger.info(row_result.__dict__)


class GroupResource(resources.ModelResource):
    description = fields.Field(attribute='groupprofile__description',
                               widget=widgets.PostSaveWidget(widgets.CharWidget()),
                               readonly=False)

    priority = fields.Field(attribute='groupprofile__priority',
                            widget=widgets.PostSaveWidget(widgets.IntegerWidget()),
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
    def after_post_save_instance(self, instance, row, using_transactions, dry_run):
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
