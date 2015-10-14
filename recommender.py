"""
Recommender class

Usage: 
    recommender.py load <FILE>
    recommender.py user <twitter_handle>
    
Options:
    <FILE>          Tab seperated file including user, timestamp, doi
    twitter_handle  Twitter username for which to return recommendations
    
AUTHORS: 
    ADD YOUR NAME HERE,
    ADD YOUR NAME HERE,
    Manos Tsagkias <manos@904labs.com>
    
DATE: 6 October 2015
"""
from time import localtime
from datetime import datetime, timedelta
from math import exp
from collections import defaultdict
import logging
import cPickle as pickle
from operator import itemgetter
import random

from docopt import docopt

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(processName)s - %(threadName)-10s) %(message)s',)

args = docopt(__doc__)

HALFLIFETIMEUNIT = 100*3600 # half the score every 6 hours


metadata = {}
raw_data = defaultdict(list)
recommendations = defaultdict(lambda: defaultdict(dict))


def default_to_regular(d):
    if isinstance(d, defaultdict):
        d = {k: default_to_regular(v) for k, v in d.iteritems()}
    return d

def build_db():
    for line in open(args['<FILE>'], 'rb'):
        fields = line.strip().split(',')
        if len(fields) > 4:
            fields[4] = ",".join(fields[4:])
        fields = fields[:4]
        
        user, timestamp, doi, title = fields
        
        try:
            timestamp = datetime.fromtimestamp(int(timestamp))
        except Exception as error:
            print "ERROR:", error
            raise
        
        obj = {"target": doi}
    
        now = timestamp
        for old_timestamp, old_doi in raw_data[user]:
            # assign a score depending on the timestamp
            origscore = exp(-0.69315 * (now - old_timestamp).seconds / HALFLIFETIMEUNIT)

            obj["source"] = old_doi
            if obj["source"] == obj["target"]:
                continue
            
            print obj["source"], obj["target"]
            
            # get previous score
            score = origscore
            prevscore = recommendations[obj["source"]][obj["target"]]
            if prevscore:
                score +=  prevscore["weight"] * exp(-0.69315 * (now - prevscore["seen"]).seconds / HALFLIFETIMEUNIT)
            recommendations[obj["source"]][obj["target"]] = {"seen": now, "weight": score}
            recommendations[obj["target"]][obj["source"]] = {"seen": now, "weight": score}

        raw_data[user].append((timestamp, doi))
        metadata[doi] = title
    
    # Store to file
    pickle.dump(metadata, open('metadata.pickle', 'wb'))
    pickle.dump(raw_data, open('raw_data.pickle', 'wb'))
    pickle.dump(default_to_regular(recommendations), open('recommendations.pickle', 'wb'))



def get_recommendations_for_single_user(user):
    if user not in raw_data:
        print "User is not in the database"
        return

    # Pull articles the user has tweeted about
    articles = raw_data[user]
    
    user_recommendations = defaultdict(lambda: 0.)
    for timestamp, doi in articles:
        # Get top-5 recommendations for each article
        if not doi in recommendations:
            continue
        for target, obj in recommendations[doi].iteritems():
            score = exp(-0.69315 * abs((obj["seen"] - timestamp)).seconds / HALFLIFETIMEUNIT) * obj["weight"]
            user_recommendations[doi] += score
    
    return_values = []
    for doi, score in sorted(user_recommendations.iteritems(), key=itemgetter(1), reverse=True):
        #print score, doi, metadata[doi]
        return_values.append([score, doi, metadata[doi]])

    return return_values

def get_twitter_friends(username):
    return [
        'chemasianj', 'skonkiel', 'shamess'
    ]

if __name__ == "__main__":
    if args['load']:
        build_db()
    elif args['user']:
        # Load stuff from files
        metadata = pickle.load(open('metadata.pickle', 'rb'))
        raw_data = pickle.load(open('raw_data.pickle', 'rb'))
        recommendations = pickle.load(open('recommendations.pickle', 'rb'))

        friends = get_twitter_friends(args['<twitter_handle>'])
        
        # Pick a user name
        # username = random.choice(raw_data.keys())
        # print "USERNAME:", username
        # get_recommendations(username)
        
        articles_scores = {}
        for friend in friends:
           friends_recommendations = get_recommendations_for_single_user(friend)

           for recommendation in friends_recommendations:
              articles_scores[recommendation[1]] = articles_scores.get(recommendation[1], 0) + recommendation[0]

        for doi, score in sorted(articles_scores.iteritems(), key=itemgetter(1), reverse=True)[:10]:
            print score, doi
