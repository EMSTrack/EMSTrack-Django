from django import forms

from .models import Ambulances, TrackableDevice, Status, Call

class AmbulanceCreateForm(forms.ModelForm):
    class Meta:
        model = Ambulances
        fields = ['license_plate', 'name', 'status']


class AmbulanceUpdateForm(forms.ModelForm):
    class Meta:
        model = Ambulances
        fields = ['license_plate', 'name', 'status']

class TrackableDeviceCreateForm(forms.ModelForm): 
    class Meta:
        model = TrackableDevice
        fields = ['device_id']

# front end team to choose which fields to display?
class CallCreateForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = '__all__'


class StatusCreateForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['name']
