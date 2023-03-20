import json
import re
from common.container.qapair import QApair
from common.container.uri import Uri
from common.container.uris import URIs
from parser.answerparser import AnswerParser


class LC_Qaud_Linked:
    def __init__(self, path="./data/LC-QUAD/linked.json"):
        self.raw_data = []
        self.qapairs = []
        self.path = path
        self.parser = LC_Qaud_LinkedParser()

    def load(self):
        with open(self.path) as data_file:
            self.raw_data = json.load(data_file)

    def parse(self):
        for raw_row in self.raw_data:
            self.qapairs.append(
                QApair(raw_row["question"], raw_row.get("answers"), raw_row["sparql_query"], raw_row, raw_row["id"],
                       self.parser))

    def print_pairs(self, n=-1):
        for item in self.qapairs[0:n]:
            print(item)
            print("")


class LC_Qaud_LinkedParser(AnswerParser):
    def __init__(self):
        #print("we are sopposed to do something here")
        super(LC_Qaud_LinkedParser, self)

    def parse_question(self, raw_question):
        return raw_question

    def parse_answerset(self, raw_answers):
        return self.parse_queryresult(raw_answers)

    def parse_sparql(self, raw_query):
        raw_query = raw_query.replace("https://", "http://")
        print("we are in lc_quad_linked and this is raw_quer",raw_query)
        uris=[]
        for uri in raw_query.split():
            #print(uri)
            uris.append(uri)
        return raw_query, True, uris
