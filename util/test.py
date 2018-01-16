def date2iso(date):
    if date is not None:
        return date.isoformat().replace('+00:00','Z')
    return date

# def point2str(point):
#     #return 'SRID=4326;' + str(point)
#     if point is not None:
#         return str(point)
#     return point

def point2str(point):
    #return 'SRID=4326;' + str(point)
    if point is not None:
        return {'latitude': str(point['latitude']),
                'longitude': str(point['longitude'])}
    return point

