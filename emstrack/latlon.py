import logging
import math


logger = logging.getLogger(__name__)

# Calculate orientation and distances based on two locations
# https://www.movable-type.co.uk/scripts/latlong.html

# Earth's radius in meters
earth_radius = 6371e3

# Stationary radius in meters
stationary_radius = 0


def calculate_orientation(location1, location2):

    # convert latitude and longitude to radians first
    lat1 = math.pi * location1.y / 180
    lat2 = math.pi * location2.y / 180
    d_lambda = math.pi * (location2.x - location1.x) / 180

    # calculate orientation and convert to degrees
    orientation = (180 / math.pi) * math.atan2(math.cos(lat1) * math.sin(lat2) -
                                               math.sin(lat1) * math.cos(lat2) *
                                               math.cos(d_lambda),
                                               math.sin(d_lambda) * math.cos(lat2))

    if orientation < 0:
        orientation += 360

    return orientation


def calculate_distance_haversine(location1, location2):

    # convert latitude and longitude to radians first
    lat1 = math.pi * location1.y / 180
    lat2 = math.pi * location2.y / 180
    d_phi = lat2 - lat1
    d_lambda = math.pi * (location2.x - location1.x) / 180

    a = math.sin(d_phi/2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lambda/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    logger.debug('|| {} - {} ||= {}'.format(location2, location1, earth_radius * c))

    return earth_radius * c


def calculate_distance_rectangular(location1, location2):

    # convert latitude and longitude to radians first
    lat1 = math.pi * location1.y / 180
    lat2 = math.pi * location2.y / 180
    d_lambda = math.pi * (location2.x - location1.x) / 180

    x = d_lambda * math.cos((lat1 + lat2) / 2)
    y = (lat2 - lat1)

    return earth_radius * math.sqrt(x * x + y * y)


# default calculate_distance
calculate_distance = calculate_distance_haversine
