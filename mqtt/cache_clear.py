from login.permissions import cache_clear
from mqtt.publish import SingletonPublishClient


def mqtt_cache_clear():

    # call cache_clear locally
    cache_clear()

    # and signal through mqtt
    SingletonPublishClient().publish_message('cache_clear')
