from django.conf import settings

if settings.TESTING:

    class Client:

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

    from nexmo import Client

# notify users that they will be updated call
client = Client(key=settings.SMS_KEY,
                secret=settings.SMS_PASS)
