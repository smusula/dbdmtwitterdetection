import datetime
from src.position import Position

class Tweet :
    def __init__(self, _id, user_id, body, hashtags, time, position):
        self.id = _id
        self.user_id = user_id
        self.body = body
        self.hashtags = hashtags
        self.time = time
        self.position = position

    def delay(self,other) :
        return abs((self.time-other.time).total_seconds())

def from_csv_entry(line):
    tokens = line.strip().split('|')

    if len(tokens) < 11:
        return None

    _id = tokens[0]
    user_id = tokens[4]
    latitude = float(tokens[2])
    longitude = float(tokens[3])
    position = Position(latitude, longitude)
    time = datetime.datetime.fromtimestamp(float(tokens[1]) / 1000)
    hashtags = tokens[8].strip().split(',')
    if len(hashtags) > 0 and len(hashtags[-1]) == 0:
        del hashtags[-1]
    hashtags = list(map(lambda x: '#' + x, hashtags))
    body = tokens[10]

    return Tweet(_id, user_id,body, hashtags, time, position)
