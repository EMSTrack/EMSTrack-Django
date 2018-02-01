from django.contrib.gis.forms import widgets

class LeafletPointWidget(widgets.BaseGeometryWidget):
    template_name = 'leaflet/leaflet.html'

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/leaflet.css',
                    'leaflet/css/location_form.css',
                    'leaflet/css/LeafletWidget.css')
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/leaflet.js',
            'leaflet/js/LeafletWidget.js'
        )

    def render(self, name, value, attrs=None):
        # add point
        if value:
            attrs.update({ 'point': { 'x': value.x,
                                      'y': value.y,
                                      'z': value.z,
                                      'srid': value.srid }
                       })
        return super().render(name, value, attrs)

