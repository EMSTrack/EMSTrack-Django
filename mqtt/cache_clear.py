from login.permissions import cache_clear
from environs import Env

env = Env()


def mqtt_cache_clear():

    # call cache_clear locally
    cache_clear()

    if env.bool("DJANGO_ENABLE_MQTT_PUBLISH", default=True):
        # and signal through mqtt
        from mqtt.publish import SingletonPublishClient
        SingletonPublishClient().publish_message('cache_clear')
