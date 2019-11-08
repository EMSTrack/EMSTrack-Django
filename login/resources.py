import logging

from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from import_export import resources, fields, widgets

from login.models import GroupAmbulancePermission, GroupHospitalPermission

logger = logging.getLogger(__name__)


class UserResource(resources.ModelResource):
    is_dispatcher = fields.Field(attribute='userprofile__is_dispatcher',
                                 widget=widgets.PostSaveWidget(widgets.BooleanWidget()),
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
    def after_post_save_instance(self, instance, row, using_transactions, dry_run):
        instance.userprofile.save()


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
