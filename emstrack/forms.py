from django.conf import settings
from django.forms.renderers import TemplatesSetting
from django.contrib.gis.forms import widgets


class LeafletPointWidget(widgets.BaseGeometryWidget):
    template_name = 'leaflet/point_widget.html'

    def render(self, name, value, attrs=None, renderer=None):
        # add point
        if value:
            attrs.update({
                'point': {'x': value.x,
                          'y': value.y,
                          'z': value.z,
                          'srid': value.srid}
            })

        # add map_provider
        attrs.update({
            'map_provider': {'provider': settings.MAP_PROVIDER, 'access_token': settings.ACCESS_TOKEN}
        })

        return super().render(name, value, attrs, TemplatesSetting())
