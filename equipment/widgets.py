from django.forms import CheckboxInput


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
        return str(super().value_from_datadict(data, files, name))

    def value_omitted_from_data(self, data, files, name):
        return str(super().value_omitted_from_data(data, files, name))
