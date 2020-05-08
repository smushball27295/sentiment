# -*- coding: utf-8 -*-
"""
Created on Fri May  8 00:55:38 2020

@author: ramesh
"""
import tweepy as tp
import pandas as pd
from datetime import datetime
from pytz import timezone
from time import sleep, time
from vaderSentiment.vaderSentiment \
import SentimentIntensityAnalyzer
import os
import json

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Twitter Authentication

with open('authToken.json') as json_file:
    authToken = json.load(json_file)
    auth = tp.OAuthHandler(authToken['consumer_key'], authToken['consumer_secret'])
    auth.set_access_token(authToken['access_token'], authToken['access_token_secret'])

api = tp.API(auth, wait_on_rate_limit=True)

# Setup sentiment analyzer
analyser = SentimentIntensityAnalyzer()

def sentiment_analysis(text):
        score  = analyser.polarity_scores(text)["compound"]
        return score

# Defining keywords

listofkeywords = ['Economy','Recession','Stagnation','US GDP','Deflation','NYSE','NASDAQ','SP500',
                  'Government spending','US Deficit','Federal Reserve','Interest Rates','Dollar value',
                  'Inflation','CPI','Non-farm payroll','Industrial output',
                  'Manufacturing level', 'US Consumer Spending']


search_term = str()
for i in range(len(listofkeywords)):
    if i == 0:
        search_term += '"' + listofkeywords[i] + '"'
    else:
        search_term += ' ' + 'OR' + ' ' + '"' + listofkeywords[i] + '"'

search_term = search_term + ' -filter:retweets'

# Import csv file and extract key information

Econ_Tweets  = pd.read_csv("Sentiment_Tweets.csv", index_col = False)

current_time = datetime.now(timezone('UTC')).replace(tzinfo= None) # Current time of scraping

# Identify tweets that are greater than 24 hours

Tweet_times = list(Econ_Tweets['Tweet Time'])

times = [i for i in range(len(Tweet_times)) if 
         (current_time - datetime.strptime(Tweet_times[i],'%Y-%m-%d %H:%M:%S')).total_seconds()/3600 > 24]

# Remove identified rows from df
Econ_Tweets = Econ_Tweets.drop(times) # Re

# Tweet main details
total_tweet_count = Econ_Tweets.shape[0] # Number of tweets currently analyzed

if len(Econ_Tweets['id']) > 0:
    sinceId = max(Econ_Tweets['id']) # The most recent tweet scraped
    maxId = min(Econ_Tweets['id']) # The oldest tweet scrpated

else:
    sinceId = None
    maxId = None 

# Identify number of tweets to be extracted

Obj_Tweets = 10000
maxTweets = Obj_Tweets-total_tweet_count

tweetCount = 0
twitter_runs = 0

start_time = time()

while tweetCount < maxTweets:
        
    tweet_reqd = min(100, maxTweets-tweetCount)
        
    if (not sinceId):
        public_tweets = api.search(q = search_term, count = tweet_reqd, lang = "en", 
                                   geocode = "39.809879,-98.556732,1340mi", result_type = "Popular")
        
        sleep(2)
           
    else:
        public_tweets = api.search(q = search_term, count = tweet_reqd, lang = "en", 
                                   geocode = "39.809879,-98.556732,1340mi", result_type = "Popular", 
                                   since_id = str(sinceId))
        
        sleep(2)
        
        if len(public_tweets) == 0:
            public_tweets = api.search(q = search_term, count = tweet_reqd, lang = "en", 
                                       geocode = "39.809879,-98.556732,1340mi", result_type = "Popular", 
                                       max_id = str(maxId))
            
            sleep(2)
            
            check_time = [tweet.id for tweet in public_tweets if 
                       (current_time - tweet.created_at).total_seconds()/3600 <= 24]
            
            if len(check_time) == 0:
                print("No More Tweets Available")
                break
            
        else:
            check_time = [tweet.id for tweet in public_tweets if 
                       (current_time - tweet.created_at).total_seconds()/3600 <= 24]
        
            if len(check_time) == 0:
                print("No More Tweets Available")
                break
           
    twitter_runs += 1
                                
    for tweet in public_tweets:
        
        if (current_time - tweet.created_at).total_seconds()/3600 <= 24:
        
            tweetCount += 1
            text = tweet.text
            user_name = tweet.user.name
            posted_time = tweet.created_at
            rt_count = tweet.retweet_count
            fav_count = tweet.favorite_count
            T_id = tweet.id
            sent_score = sentiment_analysis(text)
            
            Econ_Tweets = Econ_Tweets.append({'User Name' : user_name, 'Tweet' : text, 
                                                  'Tweet Time' : posted_time, 'RTs count' : rt_count, 
                                                  'Likes count' : fav_count, 'id' : T_id, 
                                                  'Sentiment Score' : sent_score}, ignore_index=True)
    
    sinceId = max(Econ_Tweets['id'])
    maxId = min(Econ_Tweets['id'])
                        
    elapsed_time = time() - start_time
    
    if elapsed_time > 3600:
        print ("time over")
        break
    
    print("Downloaded {0} tweets".format(tweetCount) + " On the {0} try".format(twitter_runs) + 
          " after {0}".format(elapsed_time))
                    
tweet_post_sent = [Econ_Tweets.iloc[i,6] for i in range(Econ_Tweets.shape[0]) if Econ_Tweets.iloc[i,6] >= 0]    

weighted_sent = []
for i in range(Econ_Tweets.shape[0]):
    if Econ_Tweets.iloc[i,3] > 0 and Econ_Tweets.iloc[i,4] > 0:
        weighted_sent.append(Econ_Tweets.iloc[i,3]*Econ_Tweets.iloc[i,6] + (0.5*Econ_Tweets.iloc[i,4])*Econ_Tweets.iloc[i,6])
    elif Econ_Tweets.iloc[i,3] > 0 and Econ_Tweets.iloc[i,4] <= 0:
        weighted_sent.append(Econ_Tweets.iloc[i,3]*Econ_Tweets.iloc[i,6])
    elif Econ_Tweets.iloc[i,3] <= 0 and Econ_Tweets.iloc[i,4] > 0:
        weighted_sent.append((0.75*Econ_Tweets.iloc[i,4])*Econ_Tweets.iloc[i,6])
    else:
        weighted_sent.append(Econ_Tweets.iloc[i,6])
    
tweet_post_sent = [weighted_sent[i] for i in range(len(weighted_sent)) if weighted_sent[i] >= 0]    
tweet_neg_sent = [weighted_sent[i] for i in range(len(weighted_sent)) if weighted_sent[i] < 0]        

post_percent = sum(tweet_post_sent)/(sum(tweet_post_sent)-sum(tweet_neg_sent))*100
neg_percent = -sum(tweet_neg_sent)/(sum(tweet_post_sent)-sum(tweet_neg_sent))*100

print(post_percent)
print(neg_percent)

Econ_Tweets.to_csv("Sentiment_Tweets.csv", index = False)
