from ambulance.models import Call
from emstrack.mixins import BasePermissionMixin


# Call permissions

class CallPermissionMixin(BasePermissionMixin):

    filter_field = 'ambulancecall__ambulance_id'
    profile_field = 'ambulances'
    queryset = Call.objects.all()

    def get_queryset(self):
        return super().get_queryset().distinct()
