from django.forms.models import inlineformset_factory

from .models import HospitalEquipment, Hospital

HospitalEquipmentFormset = inlineformset_factory(Hospital, HospitalEquipment, extra=1)
