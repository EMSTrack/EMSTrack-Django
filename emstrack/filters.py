from django.conf import settings
from django.template.defaulttags import register
from django.utils.safestring import mark_safe


@register.filter(is_safe=True)
def get_check(key):
    if key:
        return mark_safe('<span class="fas fa-check"></span>')
    else:
        return ''


@register.filter(is_safe=True)
def get_times(key):
    if key:
        return ''
    else:
        return mark_safe('<span class="fas fa-times"></span>')


@register.filter(is_safe=True)
def get_check_or_times(key):
    if key:
        return mark_safe('<span class="fas fa-check"></span>')
    else:
        return mark_safe('<span class="fas fa-times"></span>')


@register.simple_tag
def is_video_enabled():
    return settings.ENABLE_VIDEO