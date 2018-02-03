from django import forms
from django.contrib.gis.forms import PointField

from emstrack.forms import LeafletPointWidget

from .models import HospitalEquipment, Hospital

class HospitalCreateForm(forms.ModelForm):

    location = PointField(
        widget = LeafletPointWidget(attrs={'map_width': 500,
                                           'map_height': 300})
    )
    
    class Meta:
        model = Hospital
        fields = [ 'name',
                   'number', 'street', 'unit', # 'neighborhood',
                   'city', 'state', 'zipcode', 'country',
                   'location', 'comment' ]

class HospitalUpdateForm(HospitalCreateForm):
    
    pass
