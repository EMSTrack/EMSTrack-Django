from django import forms

from .models import Ambulance, Status, Call, Capability


class AmbulanceCreateForm(forms.ModelForm):
    class Meta:
        model = Ambulance
        fields = ['identifier', 'comment', 'status']
        

class AmbulanceUpdateForm(forms.ModelForm):
    class Meta:
        model = Ambulance
        fields = ['identifier', 'comment', 'status']


# front end team to choose which fields to display?
class CallCreateForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = '__all__'


class StatusCreateForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = '__all__'


class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = '__all__'


class CapabilityCreateForm(forms.ModelForm):
    class Meta:
        model = Capability
        fields = '__all__'
