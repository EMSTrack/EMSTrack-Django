from django.contrib.gis.forms import widgets

class LeafletPointWidget(widgets.BaseGeometryWidget):
    template_name = '../templates/leaflet/leaflet.html'

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.3.1/dist/leaflet.css',
                    'leaflet/css/location_form.css',
                    'leaflet/css/LeafletWidget.css')
        }
        js = (
            'https://unpkg.com/leaflet@1.3.1/dist/leaflet.js',
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

