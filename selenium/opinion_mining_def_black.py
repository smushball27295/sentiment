from selenium import webdriver
import time, codecs
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import re
from nltk.stem import WordNetLemmatizer
import string

# references: https://selenium-python.readthedocs.io
# ===============================================================================================
# do simple sentiment Text Blob
# ===============================================================================================
def fetch_sentiment_using_textblob(text):
    analysis = TextBlob(text)
    # set sentiment
    if analysis.sentiment.polarity >= 0:
        return 1
    else:
        return 0
# ===============================================================================================
# simple sentiment NLTK
# ===============================================================================================
def fetch_sentiment_using_SIA(text):
    sid = SentimentIntensityAnalyzer()
    polarity_scores = sid.polarity_scores(text)
    if polarity_scores["neg"] > polarity_scores["pos"]:
        return 0
    else:
        return 1
# =============================================================================================== reference:
# https://stackoverflow.com/questions/8376691/how-to-remove-hashtag-user-link-of-a-tweet-using-regular-expression
# ===============================================================================================
def strip_links(text):
    link_regex = re.compile(
        "((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)", re.DOTALL
    )
    links = re.findall(link_regex, text)
    for link in links:
        text = text.replace(link[0], ", ")
    return text
# ===============================================================================================
def strip_all_entities(text):
    entity_prefixes = ["@", "#"]
    for separator in string.punctuation:
        if separator not in entity_prefixes:
            text = text.replace(separator, " ")
    words = []
    for word in text.split():
        word = word.strip()
        if word:
            if word[0] not in entity_prefixes:
                words.append(word)
    return " ".join(words)
# ===============================================================================================
# remove_pattern
# ===============================================================================================
def remove_pattern(text, pattern_regex):
    r = re.findall(pattern_regex, text)
    for i in r:
        text = re.sub(i, "", text)
        text = text.str.replace(("[^a-zA-Z]", ""))
    return text
# ===============================================================================================
# lemmatizer
# ===============================================================================================
def lemmas(text):
    lemmatizer = WordNetLemmatizer()
    return lemmatizer.lemmatize(text)
# ===============================================================================================
# get data with selenium
# ===============================================================================================
def run(actname, count):
    count = int(count)
    twitter = "https://twitter.com/"
    url = twitter + actname
    # open the browser and visit the url
    driver = webdriver.Chrome("./chromedriver")
    driver.get(url)
    time.sleep(2)

    already_seen = set()  # keeps track of tweets we have already seen.

    # write the tweets to a file
    fw = codecs.open("opinion_mining.txt", "w", encoding="utf8")

    for i in range(count):
        
        # find all elements that have the value "tweet" for the data-testid attribute
        tweets = driver.find_elements_by_css_selector('div[data-testid="tweet"]')  #
        
        for tweet in tweets:
            if tweet in already_seen:
                continue  # we have seen this tweet before while scrolling down, ignore
            already_seen.add(
                tweet
            )  # first time we see this tweet. Mark as seen and process.

            dates, txt, comments, retweets, likes = "NA", "NA", "NA", "NA", "NA"

            try:
                txt = tweet.find_element_by_css_selector(
                    "div.css-901oao.r-hkyrab.r-1qd0xha.r-a023e6.r-16dba41.r-ad9z0x.r-bcqeeo.r-bnwqim.r-qvutc0"
                ).text
                txt = txt.replace("\n", " ")

            except:
                print("no text")

            try:

                # find the div element that havs the value "retweet" for the data-testid attribute
                retweetElement = tweet.find_element_by_css_selector(
                    'div[data-testid="retweet"]'
                )

                # find the span element that has all the specified values (space separated) in its class attribute
                retweets = retweetElement.find_element_by_css_selector(
                    "span.css-901oao.css-16my406.r-1qd0xha.r-ad9z0x.r-bcqeeo.r-qvutc0"
                ).text
                # print (retweets)
            except:
                print("no retweets")

            try:
                dataElement = tweet.find_element_by_css_selector(
                    "div.css-1dbjc4n.r-18u37iz.r-1wtj0ep.r-156q2ks.r-1mdbhws"
                )
                data = dataElement.text.split()
                comments = data[0]
                likes = data[2]
            except:
                print("no data")
            try:
                dates = tweet.find_element_by_css_selector("time").get_attribute(
                    "dateTime"
                )
            except:
                print("no date")

            # write name + tweets + date
            if txt != "NA" or retweets != "NA":
                fw.write(
                    str(actname)
                    + "\t"
                    + txt.replace("\n", " ")
                    + "\t"
                    + str(dates)
                    + "\n"
                )

        # scroll down twice to load more tweets

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    fw.close()
    driver.close()
# ===============================================================================================
# loadData = list [name,date,sentiment]
# ===============================================================================================
def loadData(fname):
    actname = []
    reviews = []
    date = []

    f = open(fname)
    for line in f:
        twname, review, dates = line.strip().split("\t")
        reviews.append(review)
        date.append(dates)
        actname.append(twname)

    reviews_clean = []
    for review in reviews:
        review = review.lower()
        review = strip_links(review)
        review = strip_all_entities(review)

        reviews_clean.append(review)

    label = []
    for line in reviews_clean:
        sentiment = fetch_sentiment_using_textblob(line)
        label.append(sentiment)

    f.close()
    return actname, reviews_clean, date, label
# ===============================================================================================
# name + comment + date + label = new text file to be used for training classifier
# ===============================================================================================
def loadFinal(file):
    actname, review, dates, label = loadData(file)
    label = []
    for line in review:
        sentiment = fetch_sentiment_using_SIA(line)
        label.append(sentiment)

    fw = codecs.open("opinion_mining_labels.txt", "w", encoding="utf8")
    for line in range(0, len(review)):
        fw.write(
            str(actname[line])
            + "\t"
            + str(review[line])
            + "\t"
            + str(dates[line])
            + "\t"
            + str(label[line])
            + "\n"
        )
    fw.close()
    return fw
# ===============================================================================================
if __name__ == "__main__":
    run("elerianm", 1000)
    loadFinal("opinion_mining.txt")
# ===============================================================================================
