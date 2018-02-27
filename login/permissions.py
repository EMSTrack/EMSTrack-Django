import logging

from functools import lru_cache

from .models import Ambulance, Hospital

logger = logging.getLogger(__name__)

PERMISSION_CACHE_SIZE = 10


@lru_cache(maxsize=PERMISSION_CACHE_SIZE)
def get_permissions(user):

    # hit the database for permissions
    return Permissions(user)


class Permissions:

    fields_id = ('ambulance_id', 'hospital_id')
    fields = ('ambulances', 'hospitals')
    models = (Ambulance, Hospital)

    def __init__(self, user, **kwargs):

        # override fields
        if 'fields' in kwargs:
            self.fields = kwargs.pop('fields')

        # override fields_id
        if 'fields_id' in kwargs:
            self.fields_id = kwargs.pop('fields_id')

        # override models
        if 'models' in kwargs:
            self.models = kwargs.pop('models')

        # initialize permissions
        self.can_read = {}
        self.can_write = {}
        for field in self.fields:
            # e.g.: self.ambulances = {}
            setattr(self, field, {})
            # e.g.: self.can_read['ambulances'] = {}
            self.can_read[field] = []
            self.can_write[field] = []

        # retrieve permissions if not None
        if user is not None:

            if user.is_superuser:

                # superuser, add all permissions
                for (model, field) in zip(self.models, self.fields):
                    # e.g.: objs = group.groupprofile.hospitals.all()
                    objs = model.objects.all()
                    # e.g.: self.hospitals.update({e.hospital_id: {...} for e in Hospitals.objects.all()})
                    getattr(self, field).update({
                        e.id: {
                            'id': e.id,
                            'can_read': True,
                            'can_write': True
                        } for e in objs})
                    logger.debug('superuser, {} = {}'.format(field, getattr(self, field)))

            else:

                # regular users, loop through groups
                for group in user.groups.all():
                    # e.g.: group.groupprofile.ambulances.all()})
                    for (field, field_id) in zip(self.fields, self.fields_id):
                        # e.g.: objs = group.groupprofile.ambulances.all()
                        objs = getattr(group.groupprofile, field).all()
                        # e.g.: self.ambulances.update({e.ambulance_id: {...} for e in objs})
                        getattr(self, field).update({
                            getattr(e,field_id): {
                                'id': getattr(e,field_id),
                                'can_read': e.can_read,
                                'can_write': e.can_write
                            } for e in objs})
                        logger.debug('group = {}, {} = {}'.format(group.name, field, getattr(self, field)))

                # add user permissions
                for (field, field_id) in zip(self.fields, self.fields_id):
                    # e.g.: objs = group.groupprofile.hospitals.all()
                    objs = getattr(user.profile, field).all()
                    # e.g.: self.hospitals.update({e.hospital_id: {...} for e in user.profile.hospitals.all()})
                    getattr(self, field).update({
                        getattr(e, field_id): {
                            'id': getattr(e, field_id),
                            'can_read': e.can_read,
                            'can_write': e.can_write
                        } for e in objs})
                    logger.debug('user, {} = {}'.format(field, getattr(self, field)))

            # build permissions
            for field in self.fields:
                for obj in getattr(self, field).values():
                    if obj['can_read']:
                        # e.g.: self.can_read['ambulances'].append(obj['id'])
                        self.can_read[field].append(obj['id'])
                    if obj['can_write']:
                        # e.g.: self.can_write['ambulances'].append(obj['id'])
                        self.can_write[field].append(obj['id'])

    def check_read_permission(self, field, id):
        try:
            return id in self.can_read[field]
        except KeyError:
            return False

    def check_write_permission(self, field, id):
        try:
            return id in self.can_write[field]
        except KeyError:
            return False

    def get_permissions(self, field, id):
        return getattr(self, field)[id]

    def get_can_read(self, field):
        return self.can_read[field]

    def get_can_write(self, field):
        return self.can_write[field]
