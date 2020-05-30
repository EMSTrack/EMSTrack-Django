import uuid

from django.conf import settings
from django.urls import reverse


def jstags(request):
    return {
        'mqtt_broker': {
            'host': settings.MQTT['BROKER_WEBSOCKETS_HOST'],
            'port': int(settings.MQTT['BROKER_WEBSOCKETS_PORT'])
        },
        'client_id': 'javascript_client_' + uuid.uuid4().hex,
        'admin_urls': [reverse('login:list-user'),
                       reverse('login:list-group'),
                       reverse('equipment:list'),
                       reverse('equipment:list-set'),
                       reverse('ambulance:location_list'),
                       reverse('login:list-client'),
                       reverse('login:restart')],
        'map_provider': {
            'provider': settings.MAP_PROVIDER,
            'access_token': settings.MAP_PROVIDER_TOKEN
        },
        'turn_server': {
            'host': setting.TURN_IP,
            'port': setting.TURN_PORT,
            'username': setting.TURN_USER,
            'password': setting.TURN_PASS,
        }
    }

