from login.permissions import cache_clear


def mqtt_cache_clear():

    # call cache_clear locally
    cache_clear()

    # and signal through mqtt
    from mqtt.publish import SingletonPublishClient
    SingletonPublishClient().publish_message('cache_clear')
