from import_export import fields


# https://github.com/django-import-export/django-import-export/issues/293
#
# address = OneToOneField(
#         attribute='address__freeform',
#         parent='address',
#         child='freeform',
#         column_name='address',
#     )

class OneToOneField(fields.Field):
    parent = ''
    child = ''

    def __init__(self, parent, child, *args, **kwargs):
        self.parent = parent
        self.child = child
        super().__init__(*args, **kwargs)

    def save(self, obj, data, is_m2m=False):
        if not self.readonly:
            child_obj = getattr(obj, self.parent, None)
            if not child_obj:
                raise ValueError('Unable to find %s on %s' % (self.parent, obj))
            setattr(child_obj, self.child, self.clean(data))
            child_obj.save()
