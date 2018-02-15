from django import forms
from django.contrib.gis.forms import PointField

from emstrack.forms import LeafletPointWidget

from .models import Ambulance, Call

class AmbulanceCreateForm(forms.ModelForm):
    
    location = PointField(
        widget = LeafletPointWidget(attrs={'map_width': 500,
                                           'map_height': 300})
    )
    
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
