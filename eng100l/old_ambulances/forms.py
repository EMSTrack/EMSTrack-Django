from django import forms

from .models import Ambulances

class AmbulanceCreateForm(forms.ModelForm):
	class Meta:
		model = Ambulances
		fields = ['license_plate']