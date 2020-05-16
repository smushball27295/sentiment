import pandas as pd
import time
import nltk
import re
import numpy as np
import pickle
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import (
    CountVectorizer,
    TfidfTransformer,
    TfidfVectorizer,
)
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
from nltk.corpus import stopwords
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
from scipy import stats
from sklearn.model_selection import cross_val_score
from nltk.stem.porter import PorterStemmer

start_time = time.time()

# reference: Python Machnine Learning by Sebastian Raschika
# ===========================================================================================
def tokenizer(text):
    return text.split()


# ===========================================================================================
def tokenzier_porter(text):
    porter = PorterStemmer()
    return [porter.stem(words) for words in text.split()]


# ===========================================================================================
def load_label_data(fname):
    actname = []
    reviews = []
    date = []
    labels = []

    f = open(fname)
    for line in f:
        twname, review, dates, label = line.strip().split("\t")

        reviews.append(review)
        date.append(dates)
        actname.append(twname)
        labels.append(int(label))

    f.close()
    return actname, reviews, date, labels


# ==================================================================================================
def balance_labels(file):

    actname, train, dates, labels = load_label_data(file)
    rev_train, rev_test, labels_train, labels_test = train_test_split(
        train, labels, test_size=0.5, random_state=0, stratify=labels
    )
    skf = StratifiedKFold(n_splits=2)
    skf.get_n_splits(train, labels)

    for train_index, test_index in skf.split(train, labels):
        rev_train, rev_test = (
            [train[i] for i in train_index],
            [train[i] for i in test_index],
        )
        labels_train, labels_test = (
            [labels[i] for i in train_index],
            [labels[i] for i in test_index],
        )

    return rev_train, labels_train, rev_test, labels_test


# ==================================================================================================
print(stats.itemfreq(labels_train))
print(stats.itemfreq(labels_test))

stop = stopwords.words("english")

tfidf = TfidfVectorizer()
cvec = CountVectorizer()
# ==================================================================================================
# LREG
# ==================================================================================================
def lreg(rev_train, labels_train, rev_test, labels_test):
    lreg_param_grid = [
        {
            "vect__ngram_range": [(1, 1), (1, 2)],
            "vect__stop_words": [stop, None],
            "vect__tokenizer": [tokenizer, tokenzier_porter],
            "clf__penalty": ["l1", "l2"],
            "clf__C": [0.001, 0.01, 1.0, 10.0, 100],
        },
        {
            "vect__ngram_range": [(1, 1), (1, 2)],
            "vect__norm": [None],
            "vect__use_idf": [False],
            "vect__stop_words": [stop, None],
            "vect__tokenizer": [tokenizer, tokenzier_porter],
            "clf__penalty": ["l1", "l2"],
            "clf__C": [0.001, 0.01, 1.0, 10.0, 100],
        },
    ]

    lreg_pipe = Pipeline(
        [
            ("vect", tfidf),
            ("clf", LogisticRegression(random_state=0, solver="liblinear")),
        ]
    )
    lreg_clfgs = GridSearchCV(
        lreg_pipe, lreg_param_grid, scoring="accuracy", cv=5, n_jobs=1, verbose=2
    )
    lreg_clfgs_fit = lreg_clfgs.fit(rev_train, labels_train)
    lreg_clfgs_best = lreg_clfgs_fit.best_estimator_
    lreg_clfgs_best.fit(rev_train, labels_train)

    predictedLREG_BEST = lreg_clfgs_best.predict(rev_test)

    return predictedLREG_BEST


# ==================================================================================================
# NB
# ==================================================================================================
def nb(rev_train, labels_train, rev_test, labels_test):
    nb_param_grid = [
        {
            "vect__ngram_range": [(1, 1), (1, 2)],
            "vect__stop_words": [stop, None],
            "vect__tokenizer": [tokenizer, tokenzier_porter],
            "vect__max_df": (0.8, 1),
            "vect__min_df": (0.01, 0.05),
            "clf__alpha": [1, 1e-1, 1e-2],
        },
        {
            "vect__ngram_range": [(1, 1), (1, 2)],
            "vect__norm": [None],
            "vect__use_idf": [False],
            "vect__stop_words": [stop, None],
            "vect__max_df": (0.8, 1.00),
            "vect__min_df": (0.01, 0.05),
            "vect__tokenizer": [tokenizer, tokenzier_porter],
            "clf__alpha": [1, 1e-1, 1e-2],
        },
    ]

    nb_classifier = Pipeline([("vect", tfidf), ("clf", MultinomialNB())])
    gridsearch_nb = GridSearchCV(
        nb_classifier, nb_param_grid, cv=5, scoring="accuracy", n_jobs=1
    )
    gridsearch_nb_fit = gridsearch_nb.fit(rev_train, labels_train)
    gridsearch_nb_best = gridsearch_nb_fit.best_estimator_
    gridsearch_nb_best.fit(rev_train, labels_train)

    predictedNB_BEST = gridsearch_nb_best.predict(rev_test)

    return predictedNB_BEST


# ==================================================================================================
if __name__ == "__main__":

    actname, reviews, date, labels = load_label_data("opinion_mining_labels.txt")
    rev_train, labels_train, rev_test, labels_test = balance_labels(
        "opinion_mining_labels.txt"
    )
    predictedNB_BEST = nb(rev_train, labels_train, rev_test, labels_test)
    predictedLREG_BEST = lreg(rev_train, labels_train, rev_test, labels_test)

    print(classification_report(labels_test, predictedNB_BEST))
    print(classification_report(labels_test, predictedLREG_BEST))

    # Print HTML
    # ==================================================================================================
    resultNB = classification_report(labels_test, predictedNB_BEST, output_dict=True)
    resultNB = pd.DataFrame(resultNB).transpose()
    htmlNB = resultNB.to_html()

    text_file_NB = open("NB.html", "w")
    text_file_NB.write(htmlNB)
    text_file_NB.close()

    resultLREG = classification_report(
        labels_test, predictedLREG_BEST, output_dict=True
    )
    resultLREG = pd.DataFrame(resultLREG).transpose()
    htmlLREG = resultLREG.to_html()

    text_file_LREG = open("LREG.html", "w")
    text_file_LREG.write(htmlLREG)
    text_file_LREG.close()
# ==================================================================================================
print("--- %s seconds ---" % (time.time() / 60 - start_time / 60))
# ==================================================================================================
# RESULTS:
# ==================================================================================================
#               precision    recall  f1-score   support

#            0       0.75      0.43      0.55       100
#            1       0.69      0.90      0.78       139

#     accuracy                           0.70       239
#    macro avg       0.72      0.66      0.66       239
# weighted avg       0.72      0.70      0.68       239

#               precision    recall  f1-score   support

#            0       0.71      0.44      0.54       100
#            1       0.68      0.87      0.77       139

#     accuracy                           0.69       239
#    macro avg       0.70      0.66      0.65       239
# weighted avg       0.69      0.69      0.67       239
# ==================================================================================================
