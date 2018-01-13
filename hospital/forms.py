from django.forms.models import inlineformset_factory

from .models import HospitalEquipment, Hospital

HospitalEquipmentFormset = inlineformset_factory(Hospital,
                                                 HospitalEquipment,
                                                 fields = ('value', 'comment'),
                                                 extra=1)
