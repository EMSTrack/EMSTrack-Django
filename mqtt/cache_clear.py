import os
from login.permissions import cache_clear


def mqtt_cache_clear():

    # call cache_clear locally
    cache_clear()

    if os.environ.get("DJANGO_ENABLE_MQTT_PUBLISH", "True"):
        # and signal through mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_message('cache_clear')
