import sys
import numpy as np
from src import tweet, event, similarity_matrix

LIMIT = 100000
TMP_PATH = 'tmp.txt'
RAM = 4000
MIN_USERS = 3

with open(sys.argv[1], 'r') as file:
    lines = list(filter(lambda x: x != '', file.read().split('\n')))

tweets = []
print('Reading tweets up to {} lines'.format(LIMIT))
for line in lines[1 : LIMIT]:
    t = tweet.from_csv_entry(line)
    if t != None:
        tweets.append(t)
tweets = np.array(tweets)

matrix = similarity_matrix.build(tweets)
clusters = event.cluster(tweets, matrix, RAM, TMP_PATH)
events = event.get_events(clusters, tweets, MIN_USERS)

out_path = sys.argv[2] if len(sys.argv) > 2 else 'data.js'
with open(out_path, 'w') as file:
    file.write('eqfeed_callback({"type":"FeatureCollection", "features":[')
    for evt in events:
        file.write(event.to_json(evt))
    file.write(']});')
