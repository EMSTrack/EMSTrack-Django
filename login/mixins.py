from mqtt.cache_clear import mqtt_cache_clear


class ClearPermissionCacheMixin:

    def save(self, *args, **kwargs):

        # save to UserProfile
        super().save(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()

    def delete(self, *args, **kwargs):

        # delete from UserProfile
        super().delete(*args, **kwargs)

        # invalidate permissions cache
        mqtt_cache_clear()
