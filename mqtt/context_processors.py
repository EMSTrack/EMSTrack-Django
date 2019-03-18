import uuid

from django.conf import settings


def jstags(request):
    return {
        'MqttBroker': {
            'host': settings.MQTT['BROKER_WEBSOCKETS_HOST'],
            'port': settings.MQTT['BROKER_WEBSOCKETS_PORT']
        },
        'clientId': 'javascript_client_' + uuid.uuid4().hex
    }