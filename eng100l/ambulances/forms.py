from django import forms

from .models import Ambulances, Status


class AmbulanceCreateForm(forms.ModelForm):
    class Meta:
        model = Ambulances
        fields = ['license_plate', 'name', 'status']


class AmbulanceEditForm(forms.ModelForm):
    class Meta:
        model = Ambulances
        fields = ['license_plate', 'name', 'status']


class StatusCreateForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['name']
