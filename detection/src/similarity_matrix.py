import math
import numpy as np
from scipy.sparse import dok_matrix, coo_matrix
from src import position
from src.position import Position, DEG_LATITUDE

def build(
    tweets,
    time_resolution = 1800,
    distance_resolution = 100,
    scale_number = 4,
    min_similarity = 0,
    min_terms = 0
):
    nb_tweets = len(tweets)

    M = dok_matrix((nb_tweets, nb_tweets), dtype = np.float)
    delta_dlat = float(distance_resolution) / DEG_LATITUDE
    delta_dlong = float(distance_resolution) / DEG_LATITUDE


    print('Pass 1')
    min_time = min(map(lambda t: t.time, tweets))
    min_lat = min(map(lambda t: t.position.latitude, tweets))
    min_lon = min(map(lambda t: t.position.longitude, tweets))
    max_time = max(map(lambda t: t.time, tweets))
    max_lat = max(map(lambda t: t.position.latitude, tweets))
    max_lon = max(map(lambda t: t.position.longitude, tweets))
    print(min_time)
    print(max_time - min_time)

    min_dist = distance_resolution
    left_upper_corner = Position(min_lat + delta_dlat / 2, min_lon + delta_dlong / 2)
    right_lower_corner = Position(max_lat + delta_dlat / 2, max_lon + delta_dlong / 2)
    max_dist= position.distance(left_upper_corner, right_lower_corner)
    scales_max_dist = _get_scales_max_dist(min_dist, max_dist, scale_number)
    temp_size = int(
        2 ** math.ceil(
            math.log(int((max_time - min_time).total_seconds() / time_resolution) + 1,2)
        )
    )
    haar_size = min(pow(2, scale_number), temp_size)
    max_supportable_scale = min(scale_number, int(math.log(haar_size, 2)))
    total_area = (max_lat - min_lat) * (max_lon - min_lon) * (DEG_LATITUDE ** 2)


    print('Pass 2')
    tf_idf = []
    idf = { }
    tweets_per_term = { }
    time_series = { }
    cells = []
    tweet_index = 0
    for tweet in tweets:
        tf = { }

        cell = (
            int((tweet.position.latitude - min_lat) / delta_dlat),
            int((tweet.position.longitude - min_lon) / delta_dlong)
        )
        cells.append(cell)

        time_index = int((tweet.time - min_time).total_seconds() / time_resolution)

        terms = tweet.hashtags
        for term in terms :
            try: tf[term] += 1
            except KeyError: tf[term] = 1

        for term, occurrence in tf.items():
            if term in idf:
                idf[term] += 1
                tweets_per_term[term].add(tweet_index)
                if cell in time_series[term]:
                    try:
                        time_series[term][cell][time_index] += occurrence
                    except KeyError:
                        time_series[term][cell][time_index] = occurrence
                else:
                    time_series[term][cell] = { time_index: occurrence }
            else :
                idf[term] = 1
                tweets_per_term[term] = set([tweet_index])
                time_series[term] = { cell: { time_index: occurrence } }
            tf[term] /= nb_tweets

        tf_idf.append(tf)
        tweet_index += 1


    print('Pass 3')
    haar_series = { }
    print('Number of terms: {}'.format(len(idf)))
    for term, nb in idf.items():
        if (nb < min_terms):
            tt = tweets_per_term[term]
            for i in tt:
                del tf_idf[i][term]
            del tweets_per_term[term]
            del time_series[term]
            continue

        idf[term] = math.log(nb_tweets / idf[term], 10)
        for cell, time_serie in time_series[term].items():
            haar = _get_finest_haar_transform(time_serie, temp_size, scale_number)
            sums = [0] * scale_number
            stds = [0] * scale_number

            for i in range(0,2) :
                sums[0] += haar[i]
                stds[0] += math.pow(haar[i], 2)

            current_scale = 1
            while current_scale < max_supportable_scale:
                sums[current_scale] += sums[current_scale - 1]
                stds[current_scale] += stds[current_scale - 1]
                alpha = int(math.pow(2, current_scale))
                for i in range(alpha, 2 * alpha):
                    sums[current_scale] += haar[i]
                    stds[current_scale] += math.pow(haar[i], 2)
                current_scale += 1

            for current_scale in range(max_supportable_scale):
                stds[current_scale] = math.sqrt(
                    math.pow(2,current_scale + 1) * stds[current_scale]
                    - math.pow(sums[current_scale], 2)
                )

            while current_scale < scale_number:
                sums[current_scale] = sums[max_supportable_scale - 1]
                stds[current_scale] = stds[max_supportable_scale - 1]
                current_scale += 1

            if cell in haar_series:
                haar_series[cell][term] = [haar, sums, stds]
            else:
                haar_series[cell] = { term:[haar, sums, stds] }


    print('Pass 4')
    for vec in tf_idf:
        norm = 0
        for term in vec:
            vec[term] *= idf[term]
            norm += math.pow(vec[term], 2)
        norm = math.sqrt(norm)
        for term in vec:
            vec[term] /= norm


    print('Pass 5')
    for i in range(nb_tweets):
        if not tf_idf[i]:
            continue

        keyset = set(tf_idf[i])
        haar_serie = haar_series[cells[i]]
        neighbours=set()

        for term in keyset:
            neighbours |= tweets_per_term[term]

        for j in neighbours:
            if j <= i:
                continue
            elif not tf_idf[j]:
                continue

            keyset_j = set(tf_idf[j])
            haar_serie_j = haar_series[cells[j]]

            intersection =keyset & keyset_j

            STFIDF = 0
            SST = None

            spatial_scale = scale_number
            dist = position.distance(tweets[i].position, tweets[j].position)
            while spatial_scale > 1 and dist > scales_max_dist[scale_number - spatial_scale]:
                spatial_scale -= 1
            temp_scale = scale_number + 1 - spatial_scale

            for term in intersection:
                STFIDF += tf_idf[i][term] * tf_idf[j][term]
                correlation = _DWT_based_correlation(
                    haar_serie[term],
                    haar_serie_j[term],
                    temp_scale
                )
                if SST == None or SST < correlation:
                    SST = correlation

            calculated_sim = SST * STFIDF
            if calculated_sim > 0 and calculated_sim >= min_similarity:
                M[i, j] = SST * STFIDF

    return coo_matrix(M)

def _get_scales_max_dist(min_dist, max_dist, scale_number):
    alpha= (max_dist / min_dist) ** (1. / (scale_number - 1))
    scales_max_dist = []
    x = min_dist
    for i in range(scale_number):
        scales_max_dist.append(x)
        x *= alpha
    return scales_max_dist

def _get_finest_haar_transform(time_serie, temp_size, scale_number):
    haar = [0] * temp_size
    time = [0] * temp_size

    for k, v in time_serie.items():
        time[k] = v

    size = temp_size
    while size > 1:
        size //= 2
        for i in range(size) :
            haar[i] = float((time[2 * i] + time[2 * i + 1])) / 2
            haar[i + size] = float((time[2 * i] - time[2 * i + 1])) / 2
        time = haar[:]
    return haar[0 : min(pow(2,scale_number), temp_size)]

def _DWT_based_correlation(haar1, haar2, temp_scale) :
    std1 = haar1[2][temp_scale - 1]
    std2 = haar2[2][temp_scale - 1]

    if std1 == std2 == 0:
        return 1
    elif std1 * std2 == 0:
        return 0

    sum1 = haar1[1][temp_scale - 1]
    sum2 = haar2[1][temp_scale - 1]
    max_size = min(pow(2, temp_scale), len(haar1[0]))
    prod_sum = 0
    for v1, v2 in zip(haar1[0][0 : max_size], haar2[0][0 : max_size]):
        prod_sum += v1 * v2
    return (max_size * prod_sum - sum1 * sum2) / (std1 * std2)
