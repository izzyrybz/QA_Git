import json, re
import requests
from common.container.qapair import QApair
from common.container.uri import Uri
from parser.answerparser import AnswerParser
# ./data/LC-QUAD/data_v8.json
# {"verbalized_question": "Who are the <comics characters> whose <painter> is <Bill Finger>?",
#  "_id": "f0a9f1ca14764095ae089b152e0e7f12",
#  "sparql_template_id": 301,
#  "sparql_query": "SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>}",
#  "corrected_question": "Which comic characters are painted by Bill Finger?"}
class LC_Qaud:
    # def __init__(self, path="./data/LC-QUAD/data_v8.json"):
    def __init__(self, path="./data/LC-QUAD/data.json"):
        self.raw_data = []
        self.qapairs = []
        self.path = path
        print("in LC_Qaud")
        self.parser = LC_QaudParser()

    def load(self):
        print("in load")
        with open(self.path) as data_file:
            self.raw_data = json.load(data_file)

    def parse(self):
        print("in parse")
        parser = LC_QaudParser()
        for raw_row in self.raw_data:
            #print(raw_row)
            sparql_query = raw_row["sparql_query"].replace("DISTINCT COUNT(", "COUNT(DISTINCT ")
            self.qapairs.append(
            #this is what gets send back to the loop in calling file
                QApair(raw_row["corrected_question"], [], sparql_query, raw_row, raw_row["_id"], self.parser))

    def print_pairs(self, n=-1):
        print("in pairs")
        for item in self.qapairs[0:n]:
            print(item)
            print("")


class LC_QaudParser(AnswerParser):
    def __init__(self):
        self.endpoint = "http://localhost:3030/test4commits/sparql"
        super(LC_QaudParser, self).__init__()
        
    def parse_sparql(self, q):
        response = requests.get(self.endpoint, params={"query": q})
        if response.status_code == 200:
            return q, True ,response.json()
        else:
            raise Exception("Query failed with status code {}".format(response.status_code))

    def parse_question(self, raw_question):
        return raw_question

    #def parse_sparql(self, raw_query):
    #    print("something with uri")

    #    return raw_query, True, uris

    def parse_answerset(self, raw_answerset):
        return []

    def parse_answerrow(self, raw_answerrow):
        return []

    def parse_answer(self, answer_type, raw_answer):
        return "", None
