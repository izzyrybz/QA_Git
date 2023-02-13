import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
#from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline

train_data = [
    {"question": "How many apples are there?", "type": "count"},
    {"question": "What are the names of the books?", "type": "list"},
    {"question": "Is the sky blue?", "type": "boolean"},
    {"question": "Did Gwen die in spiderman?", "type": "boolean"},
    {"question": "When did the first world war start?", "type": "count"},
    {"question": "What's the answer to the ultimate question of life, the universe, and everything?", "type": "unknown"},
    {"question": "How much wood would a woodchuck chuck if a woodchuck could chuck wood?", "type": "count"},
    {"question": "Muhammad Yunus has won how many awards?", "type": "count"},
    {"question": "Who wrote the musical whose composer is Emil Dean Zoghby?", "type": "list"},
    {"question": "Who is related to Kelly Osbourne & Ozzy Osbourne?", "type": "list"},
    {"question": "How many fingers do humans have?", "type": "count"},
    {"question": "How many planets are there in our solar system?", "type": "count"},
    {"question": "Do all birds have wings?", "type": "boolean"},
    {"question": "Are all reptiles cold-blooded?", "type": "boolean"},
    {"question": "How many days are there in a week?", "type": "count"},
    {"question": "Are there more dogs or cats as pets in the world?", "type": "boolean"},
    {"question": "What are the plantes with life?", "type": "list"},
    {"question": "How many states are there in the United States?", "type": "count"},
    {"question": "Is it possible to see the stars during the day?", "type": "boolean"},
    {"question": "What are the types diamonds made of carbon?", "type": "list"},
    {"question": "How many seasons are there in a year?", "type": "count"},
    {"question": "Who has Paris Hilton been married to?", "type": "boolean"},
    {"question": "Are all snakes dangerous to humans?", "type": "boolean"},
    {"question": "How many oceans are there on Earth?", "type": "count"},
    {"question": "How many commits are there on Github?", "type": "count"},
    {"question": "Does it snow in Portugal?", "type": "boolean"},
    {"question": "What is the capital of France?", "type": "list"}
]


class QuestionClassifier:
    def __init__(self):
        self.train_data = train_data
        self.df = pd.DataFrame(self.train_data)
        self.classifier = Pipeline([
            ('vectorizer', TfidfVectorizer()),
            ('classifier', RandomForestClassifier())
        ])
        self.classifier.fit(self.df['question'], self.df['type'])

    def classify_questions(self, question):
        print(question)
        return self.classifier.predict([question])
