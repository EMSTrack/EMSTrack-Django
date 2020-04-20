import logging

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User

from emstrack.sms import client

from .models import Call

logger = logging.getLogger(__name__)


# Add signal to automatically clear cache when group permissions change
@receiver(m2m_changed, sender=Call.sms_notifications.through)
def user_groups_changed_handler(sender, instance, action,
                                reverse, model, pk_set, **kwargs):

    if action == 'post_add' or action == 'post_remove':

        # get call and users
        if reverse:
            # call was added to user
            call = Call.objects.get(id=pk_set[0])
            users = {instance.id}
        else:
            # user was added to call
            call = instance
            users = []
            for id in pk_set:
                users.append(User.objects.get(id=id))

        # create message
        if action == 'post_add':
            message = _("You will be notified of updates to")
        else: # if action == 'post_remove':
            message = _("You will no longer be notified of updates to")
        message = "{}:\n* {} {}".format(message, _("Call"), call.to_string())

        # notify users
        for user in users:
            client.notify_user(user, message)
