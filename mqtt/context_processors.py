import uuid

from django.conf import settings


def jstags(request):
    return {
        'mqtt_broker': {
            'host': settings.MQTT['BROKER_WEBSOCKETS_HOST'],
            'port': int(settings.MQTT['BROKER_WEBSOCKETS_PORT'])
        },
        'client_id': 'javascript_client_' + uuid.uuid4().hex
    }