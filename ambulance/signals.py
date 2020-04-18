import nexmo

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User

from .models import Call

# notify users that they will be updated call
client = nexmo.Client(key=settings.SMS_KEY,
                      secret=settings.SMS_PASS)


# Add signal to automatically clear cache when group permissions change
@receiver(m2m_changed, sender=Call.sms_notifications.through)
def user_groups_changed_handler(sender, instance, action,
                                reverse, model, pk_set, **kwargs):

    if action == 'post_add' or action == 'post_remove':

        # get call and users
        if reverse:
            # call was added to user
            call_id = pk_set[0]
            users = {instance.id}
        else:
            # user was added to call
            call_id = instance.id
            users = []
            for id in pk_set:
                users.append(User.get(id=id))

        # create message
        if action == 'post_add':
            message = "EMSTrack\nYou will be notified of updates to call '{}'".format(call_id)

        else: # if action == 'post_remove':
            message = "EMSTrack\nYou will no longer be notified of updates to call '{}'".format(call_id)

        # notify users
        for user in users:
            client.send_message({
                'from': settings.SMS_FROM,
                'to': '18587365867',
                'text': message,
            })
