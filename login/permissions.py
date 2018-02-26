import logging

logger = logging.getLogger(__name__)


class Permissions:

    fields_id = ('ambulance_id', 'hospital_id')
    fields = ('ambulances', 'hospitals')

    def __init__(self, user, **kwargs):

        # override fields
        if 'fields' in kwargs:
            self.fields = kwargs.pop('fields')

        # override fields_id
        if 'fields_id' in kwargs:
            self.fields_id = kwargs.pop('fields_id')

        # initialize permissions
        self.can_read = {}
        self.can_write = {}
        for field in self.fields:
            # e.g.: self.ambulances = {}
            setattr(self, field, {})
            # e.g.: self.can_read['ambulances'] = {}
            self.can_read[field] = {}
            self.can_write[field] = {}

        # retrieve permissions if not None
        if user is not None:

            # loop through groups
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

    def get_read_permissions(self, field):
        return self.can_read[field]

    def get_write_permissions(self, field):
        return self.can_write[field]
