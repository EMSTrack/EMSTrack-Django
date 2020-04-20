import logging

from django.conf import settings

logger = logging.getLogger(__name__)

if settings.SMS_PROVIDER == 'nexmo':

    from nexmo import Client as BaseClient

else:

    class BaseClient:

        def __init__(self, **kwargs):
            self.messages = []

        def send_message(self, message):
            assert 'to' in message
            assert 'from' in message
            assert 'text' in message
            self.messages.append(message)

        def reset(self):
            self.messages = []


class Client(BaseClient):

    def notify_user(self, user, message):
        mobile_number = user.userprofile.mobile_number
        if mobile_number:
            sms = {
                'from': settings.SMS_FROM,
                'to': mobile_number.as_e164,
                'text': 'Message from EMSTrack:\n' + message,
            }
            client.send_message(sms)
            logger.debug('SMS sent: {}'.format(sms))
        else:
            logger.debug('SMS not sent: user {} does not have a mobile on file'.format(user))


# notify users that they will be updated call
client = Client(key=settings.SMS_KEY,
                secret=settings.SMS_PASS)
