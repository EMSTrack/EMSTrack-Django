from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from import_export import resources, fields, widgets


class UserResource(resources.ModelResource):
    is_dispatcher = fields.Field(attribute='userprofile__is_dispatcher',
                                 widget=widgets.BooleanWidget(),
                                 readonly=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_dispatcher', 'is_active')
        export_order = ('id', 'username', 'first_name', 'last_name', 'email',
                        'is_staff', 'is_dispatcher', 'is_active')

    # save userprofile related fields
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not using_transactions and dry_run:
            # we don't have transactions and we want to do a dry_run
            pass
        else:
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
