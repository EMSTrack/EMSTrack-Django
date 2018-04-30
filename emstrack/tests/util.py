from drf_extra_fields.geo_fields import PointField
from django.contrib.gis.geos import GEOSGeometry


def date2iso(date):
    if date is not None:
        return date.isoformat().replace('+00:00', 'Z')
    return date


# def point2str(point):
#     #return 'SRID=4326;' + str(point)
#     if point is not None:
#         return str(point)
#     return point


def point2str(point):
    # return 'SRID=4326;' + str(point)
    if point is None:
        return None
    if isinstance(point, GEOSGeometry):
        return PointField().to_representation(point)
    elif isinstance(point, dict):
        # return {'latitude': str(point['latitude']),
        #         'longitude': str(point['longitude'])}
        return {'latitude': point['latitude'],
                'longitude': point['longitude']}
    else:
        raise Exception("Unknown point type")


def dict2point(value):
    return PointField().to_internal_value(value)
