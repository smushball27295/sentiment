#!/usr/bin/python3

import GetOldTweets3 as got
import re
import contractions
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import LancasterStemmer, WordNetLemmatizer
from emot.emo_unicode import UNICODE_EMO, EMOTICONS
import csv
import time
import sys
from datetime import datetime
from datetime import timedelta
import dateutil.parser as dp
from textblob import TextBlob
import string
import multiprocessing as mp

def timer(name):
    return
    if name in timer.timers:
        print("{} took {} seconds".format(name, (time.time() - timer.timers[name])))
        del timer.timers[name]
    else:
        timer.timers[name] = time.time()
timer.timers = {}

def getTweetId(dt):
    msepoch = int(dt.timestamp() * 1000)
    tweetId = (msepoch - 1288834974657) << 22;
    return tweetId

def getQuery(startId, endId, search):
    result = "since_id:{} max_id:{} {}"\
                .format(startId, endId, search);
    return result;

def convert_emot(text):
    for emot in EMOTICONS:
        text = re.sub(u'('+emot+')', \
                      "_".join(EMOTICONS[emot].replace(",","").split()), text)
    return text

def cleanup(text):
    timer("cleanup")
    # conver emoticons to words
    text = convert_emot(text)

    # remove non-english characters
    text = ' '.join(re.sub("([^\x00-\x7F])+"," ",text).split())

    # remove html entities
    #text = ''.join(xml.etree.ElementTree.fromstring(text))
    text = ' '.join(re.sub(re.compile(r'<[^>]+>'), " ", text).split())

    # remove non-ascii
#    text = text.encode('ascii','ignore')

    # remove urls
    text = ' '.join(re.sub(r"http\S+", " ", text).split())
    text = ' '.join(re.sub("(\w+:\/\/\S+)", " ", text).split())

    # remove hashtags and mentions
    text = ' '.join(re.sub("(@[A-Za-z0-9_]+)|(#[A-Za-z0-9_]+)", " ", text).split())

    # replace contractions
    text = contractions.fix(text)

    # remove certain punctuations
    #text = ' '.join(re.sub("[\:\;\-\=\_\|\/\)\(\.\,]", " ", text).split())
    text = text.translate(str.maketrans(' ', ' ', string.punctuation))

    # remove numbers
    text = ' '.join(re.sub("[0-9]", " ", text).split())

    # split attached words
    #text = ' '.join(re.findall('[A-Z][^A-Z]*', text))

    # make lowercase
    text = text.lower()
    timer("cleanup")
    return text


def getPolarity(text):
    # correct spelling
    timer("polarity")
    text = TextBlob(text).correct()
    polarity = text.sentiment.polarity
    timer("polarity")
    return polarity

def getTweets(query):
    tweetCriteria = got.manager.TweetCriteria() \
                        .setQuerySearch(query) \
                        .setLang('en') \
                        .setEmoji("unicode")
    rows = []
    tweets = []
    delay  = 1

    timer("query")
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

    timer("query")
    timer("process")

    for tweet in tweets:
        clean_text = cleanup(tweet.text)
        if len(clean_text) >= 4:
            row = [ tweet.id, \
                    tweet.date, \
                    tweet.username, \
                    clean_text, \
                    getPolarity(clean_text), \
                    getMasterScore(clean_text), \
                    tweet.retweets, \
                    tweet.favorites \
            ]
            rows.append(row)
    timer("process")

    return rows

def loadMasterDictionary():
    filename = 'LoughranMcDonald_MasterDictionary_2018.csv'
    master   = {}
    with open(filename) as csvfile:
        linereader = csv.reader(csvfile, delimiter=',')
        linereader.__next__() # skip column names line
        for row in linereader:
            word = row[0].lower()
            master[word] = 0
            if (int(row[7]) > 0):
                master[word] = -1
            if (int(row[8]) > 0):
                master[word] = 1
    return master


master = loadMasterDictionary()
def getMasterScore(text):
    timer("master")
    score = 0
    activewords = 0
    words = word_tokenize(text)
    for word in words:
        if word in master.keys():
            score += master[word]
            if master[word] != 0:
                activewords += 1
    if activewords > 0:
        score /= activewords
    timer("master")
    return score


def writer(resultQueue):
    filename = "./output.csv"
    fields = ["Tweet Id", "Tweet Date", "Username", "Text",\
                "TextBlob", "MasterDict", "Retweets", "Favorites"]
    resultDict = {}
    nextItem = 0
    with open(filename, 'w+') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fields)
        res = resultQueue.get()
        while (not (res == 'stop' and len(resultDict) == 0)):
            while res == 'stop':
                res = resultQueue.get()
                resultQueue.put('stop')
            resultDict[res[0]] = res[1]
            wrote = False
            while nextItem in resultDict:
                writer.writerows(resultDict[nextItem])
                del resultDict[nextItem]
                print("wrote ", nextItem)
                nextItem += 1
                wrote = True
            if wrote:
                csvfile.flush()
            res = resultQueue.get()

def worker(w, resultQueue):
    rows = getTweets(w[1])
    resultQueue.put((w[0], rows))

def main():
    # start the manager / forked processes
    manager = mp.Manager()
    resultQueue = manager.Queue()
    pool = mp.Pool(10)
    writeProc = pool.apply_async(writer, (resultQueue,))

    hours = 24;
    dt_start = dp.parse(sys.argv[1])
    #dt_start = dp.parse("05/08/2020 08:00:00")
    search = sys.argv[2] # "bitcoin"
    id_start = getTweetId(dt_start)

    jobs = []
    #for i in range(2):
    for i in range(12 * hours):
        dt_end = dt_start + timedelta(minutes=5)
        id_end = getTweetId(dt_end)
        work = (i, getQuery(id_start, id_end, search))
        job = pool.apply_async(worker, (work, resultQueue))
        jobs.append(job)
        #rows = getTweets(getQuery(id_start, id_end, search))
        dt_start = dt_end
        id_start = id_end

    # wait for the workers to finish
    for job in jobs:
        job.get()
    # stop the writer
    resultQueue.put('stop')
    writeProc.get()
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()



# Sources Used:
# https://medium.com/towards-artificial-intelligence/emoticon-and-emoji-in-text-mining-7392c49f596a
# https://github.com/Mottl/GetOldTweets3/issues/3#issuecomment-527642499
# https://stackoverflow.com/questions/6999726/how-can-i-convert-a-datetime-object-to-milliseconds-since-epoch-unix-time-in-p
# https://towardsdatascience.com/twitter-sentiment-analysis-using-fasttext-9ccd04465597
# https://gist.github.com/MrEliptik/b3f16179aa2f530781ef8ca9a16499af
# https://www.analyticsvidhya.com/blog/2014/11/text-data-cleaning-steps-python/
# multiprocessing:
# https://stackoverflow.com/questions/13446445/python-multiprocessing-safely-writing-to-a-file
