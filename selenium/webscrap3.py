#!/usr/bin/python
from selenium import webdriver
import time,codecs
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import re
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# do simple sentiment NLTK + Text Blob

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> >>>>>>   

def fetch_sentiment_using_textblob(text):
    analysis = TextBlob(text)
    # set sentiment 
    if analysis.sentiment.polarity >= 0:
        return 1
    else: 
        return 0



def fetch_sentiment_using_SIA(text):
    sid = SentimentIntensityAnalyzer()
    polarity_scores = sid.polarity_scores(text)
    if polarity_scores['neg'] > polarity_scores['pos']:
        return 0
    else:
        return 1
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# load list

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def loadData(fname):
    reviews=[]
    date=[]
    f=open(fname)
    for line in f:
        review,dates=line.strip().split('\t')  
        reviews.append(review)    
        date.append(dates)
    f.close()     
    return reviews,date


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# get data with selenium

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# 1. expert opinion, opinion mining
url='https://twitter.com/elerianm'           

# 2. by search term
#url = 'https://twitter.com/search?q=layoffs'   

#open the browser and visit the url
driver = webdriver.Chrome('./chromedriver')
driver.get(url)
time.sleep(2)

already_seen=set()#keeps track of tweets we have already seen.

#write the tweets to a file
fw=codecs.open('opinion_mining.txt','w',encoding='utf8')

for i in range(100):

    print(i)
    #find all elements that have the value "tweet" for the data-testid attribute
    tweets=driver.find_elements_by_css_selector('div[data-testid="tweet"]')#
    print(len(tweets))
    for tweet in tweets:

        if tweet in already_seen:continue#we have seen this tweet before while scrolling down, ignore
        already_seen.add(tweet)#first time we see this tweet. Mark as seen and process.
        
        dates,txt,comments,retweets,likes='NA','NA','NA','NA','NA'
        
        try: 
            txt=tweet.find_element_by_css_selector("div.css-901oao.r-hkyrab.r-1qd0xha.r-a023e6.r-16dba41.r-ad9z0x.r-bcqeeo.r-bnwqim.r-qvutc0").text
            txt=txt.replace('\n', ' ')
        except: print ('no text')     

        try:
        
            #find the div element that havs the value "retweet" for the data-testid attribute
            retweetElement=tweet.find_element_by_css_selector('div[data-testid="retweet"]')
 
            #find the span element that has all the specified values (space separated) in its class attribute
            retweets=retweetElement.find_element_by_css_selector('span.css-901oao.css-16my406.r-1qd0xha.r-ad9z0x.r-bcqeeo.r-qvutc0').text  
            #print (retweets)                                    
        except:
            print ('no retweets')

        try:
            dataElement = tweet.find_element_by_css_selector('div.css-1dbjc4n.r-18u37iz.r-1wtj0ep.r-156q2ks.r-1mdbhws')
            data = dataElement.text.split()
            print(data)
            comments = data[0]
            likes = data[2]
        except:
            print('no data')
        try:
            dates = tweet.find_element_by_css_selector("time").get_attribute("dateTime")
        except:
            print("no date")

        #only write tweets that have text or retweets (or both). 
        if txt!='NA' or retweets!='NA':
            fw.write(txt.replace('\n',' ')+'\t'+str(dates)+'\n')
        

        #scroll down twice to load more tweets
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

fw.close()

driver.close()
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# create new file: comment + date + label
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

review,dates=loadData('opinion_mining.txt')  

label=[]
for line in review:
    sentiment=fetch_sentiment_using_textblob(line)
    label.append(sentiment)

fw=codecs.open('opinion_mining_labels.txt','w',encoding='utf8')
for line in range(0,len(review)):
    fw.write(str(review[line]) +'\t'+ str(dates[line])+'\t'+str(label[line])+'\n')

    print(str(review[line]) +'\t'+ str(dates[line])+'\t'+str(label[line])+'\n')
fw.close()







