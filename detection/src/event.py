import subprocess
import numpy as np
import math
from src import tweet
from src.position import Position

class Event:
    def __init__(self, tweets, top = 3):
        self.tweets = sorted(tweets, key = lambda t: t.time)
        self.starting_time = self.tweets[0].time
        self.estimated_duration = tweet.delay(
            self.tweets[len(tweets) // 10],
            self.tweets[9 * len(tweets) // 10]
        )

        user_ids = set()
        self.center = Position(0, 0)
        for t in tweets:
            user_ids.add(t.user_id)
            self.center.latitude += t.position.latitude
            self.center.longitude += t.position.longitude

        self.center.latitude /= len(tweets)
        self.center.longitude /= len(tweets)

        self.nb_users = len(user_ids)

        hashtags = { }
        for t in self.tweets:
            for h in t.hashtags:
                try:
                    hashtags[h.lower()] += 1
                except KeyError:
                    hashtags[h.lower()] = 1

        self.hashtags = sorted(
            hashtags.items(),
            key = lambda h: h[1],
            reverse = True
        )[0 : min(top, len(hashtags))]
        self.hashtags = list(map(lambda h: h[0], self.hashtags))

def to_json(evt):
    out = '{"type":"Feature", "properties":{'
    body = evt.tweets[0].body.replace('"', '\\"')
    out += '"people":{}, "tweet":"{}"'.format(math.log(evt.nb_users), body)
    out += '},"geometry":{"type":"Point","coordinates":['
    out += '{},{}'.format(evt.center.longitude, evt.center.latitude)
    out += ']}},'
    return out

def cluster(tweets, matrix, RAM, file_path):
    n = matrix.shape[0]
    print('Calling ModularityOptimizer')

    l = sorted(zip(matrix.row, matrix.col, matrix.data))
    if (l[-1][1] < n - 1):
        l.append((n - 2,n - 1, 0))

    lines = '\n'.join(['{}\t{}\t{}'.format(i,j,v) for i, j, v in l])
    with open(file_path, 'w') as file:
        file.write(lines)

    cmd = "java -Xmx{0}m -jar ModularityOptimizer.jar {1} {1} 1 0.5 2 10 10 0 0".format(
        RAM,
        file_path
    )
    process = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
    process.wait()

    with open(file_path, 'r') as file:
        clusters = list(map(int, file.readlines()))
        return np.array(clusters)

def get_events(clusters, tweets, min_users):
    events = []
    unique = set(clusters)
    for cluster_id in unique:
        cluster_tweets = tweets[clusters == cluster_id]
        evt = Event(cluster_tweets)
        if evt.nb_users >= min_users:
            events.append(evt)
    return events
