import src.tweet as tweet
import src.similarity_matrix as similarity_matrix

with open('input.txt', 'r') as file:
    lines = list(filter(lambda x: x != '', file.read().split('\n')))

tweets = []
LIMIT = 1000
print('Reading tweets up to {} lines'.format(LIMIT))
for line in lines[1 : LIMIT]:
    t = tweet.from_csv_entry(line)
    if t != None:
        tweets.append(t)

matrix = similarity_matrix.build(tweets)
