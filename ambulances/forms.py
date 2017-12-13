from django import forms

from .models import Ambulance, Call

class AmbulanceCreateForm(forms.ModelForm):
    class Meta:
        model = Ambulance
        fields = ['identifier', 'comment']
        

class AmbulanceUpdateForm(forms.ModelForm):
    class Meta:
        model = Ambulance
        fields = ['identifier', 'comment']


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
