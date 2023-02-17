import requests
import json
import pandas as pd
import numpy as np
import json
import spacy
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import itertools
import spotlight
import tagme
import inflect
import re
import sys
import requests
from nltk.stem.porter import *
import nltk
from nltk import word_tokenize, pos_tag, ne_chunk
import json
import networkx as nx
stemmer = PorterStemmer()

import rdflib

def json_to_knowledgegraph(data):

    #print(data)

    knowledge_graph = []

    for item in data['results']['bindings']:
        subject = item['subject']['value']
        predicate = item['predicate']['value']
        object = item['object']['value']
        knowledge_graph.append((subject, predicate, object))
    with open("turtle/knowledge_graph.ttl", "w") as f:
        for triplet in knowledge_graph:
            subject, predicate, object = triplet
            #print("<{}> <{}> {} .".format(subject, predicate, json.dumps(object)))
            f.write("<%s> <%s> '%s' .\n" % (subject, predicate, object))


class KnowledgeGraphGenerator:
    def __init__(self):
        #get knowledgegraph
        jena_sparql_endpoint = 'http://localhost:3030/dbpedia/query'
        get_tripples_query = '''
        SELECT ?subject ?predicate ?object
        WHERE {
        ?subject ?predicate ?object
        }
        '''
        jena_response = requests.get(jena_sparql_endpoint, params={"query": get_tripples_query})
        #print(jena_response.json)
        json_to_knowledgegraph(jena_response.json())


#KnowledgeGraphGenerator()