import logging

from django.conf import settings

logger = logging.getLogger(__name__)


if settings.TESTING:

    class BaseClient:

        def __init__(self, **kwargs):
            self.messages = []

        def send_message(self, message):
            assert 'to' in message
            assert 'from' in message
            assert 'text' in message
            self.messages.append(message)

        def reset_messages(self):
            self.messages = []

else:

    from nexmo import Client as BaseClient


class Client(BaseClient):

    def notify_user(self, user, message):
        mobile_number = user.userprofile.mobile_number
        if mobile_number:
            sms = {
                'from': settings.SMS_FROM,
                'to': mobile_number,
                'text': 'Message from EMSTrack:\n' + message,
            }
            client.send_message(sms)
            logger.debug('SMS sent: {}'.format(sms))
        else:
            logger.debug('SMS not sent: user {} does not have a mobile on file'.format(user))


# notify users that they will be updated call
client = Client(key=settings.SMS_KEY,
                secret=settings.SMS_PASS)
