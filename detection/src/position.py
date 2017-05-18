import math

DEG_LATITUDE = 111320 # in meters

class Position :
    def __init__(self, latitude, longitude):
        self.latitude=latitude
        self.longitude=longitude

def distance(pos1, pos2):
    return math.sqrt(
        math.pow(pos1.longitude - pos2.longitude,2)
        + math.pow(pos1.latitude - pos2.latitude,2)
    ) * DEG_LATITUDE
