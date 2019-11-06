from django.utils.translation import ugettext_lazy as _


def make_choices(choices):
    """
    Returns tuples of choices based on the enum choices parameter.
    """
    return [(m.name, m.value) for m in choices]


def make_choices_and_translate(choices):
    """
    Returns tuples of localized choices based on the enum choices parameter.
    Uses lazy translation for choices names.
    """
    return [(m.name, _(m.value)) for m in choices]

