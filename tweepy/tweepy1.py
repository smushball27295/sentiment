# -*- coding: utf-8 -*-
"""
Created on Fri May  8 00:55:38 2020

@author: ramesh
"""
import tweepy as tp

import pandas as pd

import json

 

# Twitter Authentication

 

with open('authToken.json') as json_file:

    authToken = json.load(json_file)

    auth = tp.OAuthHandler(authToken['consumer_key'], authToken['consumer_secret'])

    auth.set_access_token(authToken['access_token'], authToken['access_token_secret'])

 

api = tp.API(auth, wait_on_rate_limit=True)

 

# Import csv file and extract key information

 

Econ_Tweets  = pd.read_csv("Sentiment_Tweets.csv", index_col = False)

 

maxTweets = 10000

 

sinceId = None

 

tweetCount = 0

twitter_runs = 0

 

while tweetCount < maxTweets:

       

    tweet_reqd = min(100, maxTweets-tweetCount)

       

    if (not sinceId):

        public_tweets = api.search(q = "Economy", count = tweet_reqd, lang = "en",

                                   geocode = "39.809879,-98.556732,1340mi", result_type = "Popular")

       

         

    else:

        public_tweets = api.search(q = "Economy", count = tweet_reqd, lang = "en",

                                   geocode = "39.809879,-98.556732,1340mi", result_type = "Popular",

                                   since_id = str(sinceId))

          

    twitter_runs += 1

                                

    for tweet in public_tweets:

       

            tweetCount += 1

            text = tweet.text

            user_name = tweet.user.name

            posted_time = tweet.created_at

            rt_count = tweet.retweet_count

            fav_count = tweet.favorite_count

            T_id = tweet.id

           

            Econ_Tweets = Econ_Tweets.append({'User Name' : user_name, 'Tweet' : text,

                                                  'Tweet Time' : posted_time, 'RTs count' : rt_count,

                                                  'Likes count' : fav_count, 'id' : T_id}, ignore_index=True)

   

    sinceId = max(Econ_Tweets['id'])

   

    print("Downloaded {0} tweets".format(tweetCount) + " On the {0} try".format(twitter_runs))

                   

Econ_Tweets.to_csv("Sentiment_Tweets.csv", index = False)
