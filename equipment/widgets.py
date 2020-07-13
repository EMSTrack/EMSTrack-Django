import logging
from django.forms import CheckboxInput

logger = logging.getLogger(__name__)


def check_boolean(value):
    # Translate true and false strings to boolean values.
    values = {'true': True, 'false': False}
    if isinstance(value, str):
        value = values.get(value.lower(), value)
    return bool(value)


class StringCheckboxInput(CheckboxInput):

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, check_test=check_boolean)

    def value_from_datadict(self, data, files, name):
        value = str(super().value_from_datadict(data, files, name))
        logger.debug('value = %s', value)
        return value

    def format_value(self, value):
        """Only return the 'value' attribute if value isn't empty."""
        if self.check_test(value) or value is None or value == '':
            return
        return str(value)
