import uuid

from django.conf import settings


def jstags(request):
    return {
        'MQTTBroker': {
            'host': settings.MQTT_WEBSOCKETS_HOST,
            'port': settings.MQTT_WEBSOCKETS_PORT
        },
        'client_id': 'javascript_client_' + uuid.uuid4().hex
    }