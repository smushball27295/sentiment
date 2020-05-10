#!/usr/bin/python3
import GetOldTweets3 as got
import re
import csv
import sys
import time
from datetime import datetime
from datetime import timedelta
import dateutil.parser as dp


def getTweetId(dt):
    msepoch = int(dt.timestamp() * 1000)
    tweetId = (msepoch - 1288834974657) << 22;
    return tweetId

def getQuery(startId, endId, search):
    result = "since_id:{} max_id:{} {}"\
                .format(startId, endId, search);
    return result;

def cleanup(text):
    quote=re.compile(r'"')
    comma=re.compile(r',')
    if re.search(comma, text) is not None:
        (text, n) = quote.subn("'", text)
        text = '"'+text+'"'
    return text

def getTweets(query):
    tweetCriteria = got.manager.TweetCriteria()\
        .setQuerySearch(query)
    rows = []
    tweets = []
    delay  = 1

    failed = True
    while failed:
        failed = False
        try:
            tweets = reversed(got.manager.TweetManager.getTweets(tweetCriteria))
        except SystemExit:
            failed = True
            print("too many requests, sleeping for {} seconds".format(delay))
            time.sleep(delay)
            delay *= 2

    for tweet in tweets:
        row = [ tweet.id, \
                tweet.date, \
                tweet.username, \
                cleanup(tweet.text), \
                tweet.retweets, \
                tweet.permalink ]
        rows.append(row)

    return rows


def main():
    hours = 1;
    dt_start = dp.parse(sys.argv[1])
    coin = sys.argv[2]
    id_start = getTweetId(dt_start)


    filename = "./output.csv"        
    fields = ["Tweet Id", "Tweet Date", "Username", "Text",\
                    "Retweets", "Permalink"]
    with open(filename, 'w+') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fields)

        for i in range(2): # 10 minutes
        #for i in range(12 * hours):
            dt_end = dt_start + timedelta(minutes=5)
            id_end = getTweetId(dt_end)

            rows = getTweets(getQuery(id_start, id_end, coin))
            writer.writerows(rows)

            dt_start = dt_end
            id_start = id_end

if __name__ == "__main__":
    main()





# https://github.com/Mottl/GetOldTweets3/issues/3#issuecomment-527642499
# stackoverflow.com/questions/6999726/how-can-i-convert-a-datetime-object-to-milliseconds-since-epoch-unix-time-in-p


