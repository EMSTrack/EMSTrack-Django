from django.contrib.auth.models import User
from django.conf import settings
from django import forms
from django.contrib.gis import forms as gis_forms
from django.contrib.gis.forms import widgets as gis_widgets
from django.core.serializers import serialize

from .models import Ambulances, TrackableDevice, Status, Call

class LeafletPointWidget(gis_widgets.BaseGeometryWidget):
    template_name = 'leaflet/leaflet.html'

    class Media:
        css = {
            'all': ('leaflet/css/LeafletWidget.css',)
        }
        js = (
            'http://cdn.leafletjs.com/leaflet/v0.7.7/leaflet.js',
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

class AmbulanceCreateForm(forms.ModelForm):
  class Meta:
    model = Ambulances
    fields = ['license_plate', 'name']


class StatusCreateForm(forms.ModelForm):
  class Meta:
    model = Status
    fields = ['name']

class AmbulanceUpdateForm(forms.ModelForm):
  class Meta:
    model = Ambulances
    fields = [ 'status']

class TrackableDeviceCreateForm(forms.ModelForm):
  class Meta:
    model = TrackableDevice
    fields = ['device_id']

# front end team to choose which fields to display?
class CallCreateForm(forms.ModelForm):
  class Meta:
    model = Call
    fields = '__all__'
