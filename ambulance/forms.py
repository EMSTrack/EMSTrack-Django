from django import forms
from django.contrib.gis.forms import PointField
from django.utils import timezone

from emstrack.forms import LeafletPointWidget

from .models import Ambulance, Call, Location


class AmbulanceCreateForm(forms.ModelForm):
    location = PointField(
        widget=LeafletPointWidget(attrs={'map_width': 500,
                                         'map_height': 300})
    )

    class Meta:
        model = Ambulance
        fields = ['identifier', 'capability', 'status', 'comment', 'location']


class AmbulanceUpdateForm(AmbulanceCreateForm):

    def clean(self):
        # call super
        super().clean()

        # if updating status or location
        if 'status' in self.changed_data or 'location' in self.changed_data:
            # See https://stackoverflow.com/questions/5275476/django-alter-form-data-in-clean-method
            # Mauricio: I think this odd behavior is because timestamp is not present in the form

            # update timestamp as well
            now = timezone.now()
            self.cleaned_data["timestamp"] = now
            self.instance.timestamp = now

        return self.cleaned_data


# Location forms

class LocationAdminCreateForm(forms.ModelForm):
    location = PointField(
        widget=LeafletPointWidget(attrs={'map_width': 500,
                                         'map_height': 300})
    )

    class Meta:
        model = Location
        fields = ['name', 'type',
                  'number', 'street', 'unit', 'neighborhood',
                  'city', 'state', 'zipcode', 'country',
                  'location', 'comment']


class LocationAdminUpdateForm(LocationAdminCreateForm):
    pass


# front end team to choose which fields to display?

class CallCreateForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = '__all__'


class CallUpdateForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = '__all__'

class CallPatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'

class CallAmbulanceForm(forms.ModelForm):
    class Meta:
        model = Ambulance
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
