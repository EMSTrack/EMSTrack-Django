import logging

from import_export import fields, widgets

logger = logging.getLogger(__name__)


# https://github.com/django-import-export/django-import-export/issues/293

class OneToOneField(fields.Field):

    def save(self, obj, data, is_m2m=False):
        logger.info('> In OneToOneField save')
        logger.info('data = %s, obj = %s, userprofile = %', data.__dict__, obj.__dict__, obj.userprofile)
        super().save(obj, data, False)
        logger.info('data = %s, obj = %s, userprofile = %', data.__dict__, obj.__dict__, obj.userprofile.__dict__)


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
        logger.info('> In DeferredSaveWidgdet clean: row = ')
        logger.info(row)
        return self.widget.clean(value, row, *args, **kwargs)

    def render(self, value, obj=None):
        return self.widget.render(value, obj)
