from django.contrib.auth.models import User

from ambulances.models import Ambulance, Hospital

# Ambulance and Hospital Permissions

class AmbulancePermission(models.Model):

    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)

    def __str__(self):
        return  '{}(id={}): read[{}] write[{}]'.format(self.ambulance.identifier,
                                                       self.ambulance.id,
                                                       self.can_read,
                                                       self.can_write)
class HospitalPermission(models.Model):

    hospital = models.ForeignKey(Hospital,
                                  on_delete=models.CASCADE)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)

    def __str__(self):
        return  '{}(id={}): read[{}] write[{}]'.format(self.hospital.name,
                                                       self.hospital.id,
                                                       self.can_read,
                                                       self.can_write)


# Profile and state

class Profile(models.Model):

    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)
    ambulances = models.ManyToManyField(AmbulancePermission)
    hospitals = models.ManyToManyField(HospitalPermission)

    def __str__(self):
        return ('> Ambulances:\n' +
                '\n'.join('  {}'.format(k) for k in self.ambulances.all()) +
                '\n> Hospitals:\n' +
                '\n'.join('  {}'.format(k) for k in self.hospitals.all()))
    
class State(models.Model):

    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.CASCADE,
                                 null=True, blank=True)
    ambulance = models.ForeignKey(Ambulance,
                                  on_delete=models.CASCADE,
                                  null=True, blank=True)

