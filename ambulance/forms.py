from django import forms

from django.contrib.gis import forms as gis_forms
from django.contrib.gis.forms import widgets as gis_widgets

from .models import Ambulance, Call

class LeafletPointWidget(gis_widgets.BaseGeometryWidget):
    template_name = 'leaflet/leaflet.html'

    class Media:
        css = {
            'all': ('leaflet/css/LeafletWidget.css')
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

    location = gis_forms.PointField(
        widget = LeafletPointWidget(attrs={'map_width': 500,
                                           'map_height': 300}))
    
    class Meta:
        model = Ambulance
        fields = [ 'identifier', 'capability', 'status', 'comment', 'location' ]

class AmbulanceUpdateForm(AmbulanceCreateForm):
    
    pass
        
# front end team to choose which fields to display?
class CallCreateForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = '__all__'


# class AmbulanceStatusCreateForm(forms.ModelForm):
#     class Meta:
#         model = AmbulanceStatus
#         fields = '__all__'


# class AmbulanceStatusUpdateForm(forms.ModelForm):
#     class Meta:
#         model = AmbulanceStatus
#         fields = '__all__'


# class AmbulanceCapabilityCreateForm(forms.ModelForm):
#     class Meta:
#         model = AmbulanceCapability
#         fields = '__all__'
