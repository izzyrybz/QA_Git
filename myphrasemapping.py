
import copy
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
from rdflib import Graph, URIRef, Literal
stemmer = PorterStemmer()
p = inflect.engine()
tagme.GCUBE_TOKEN = ""

def process_knowledge_graph(filepath):
    graph = Graph()
    all_the_properties=[]
    properties={}

    with open(filepath, 'r') as file:
        turtle_entry = file.read()
# Parse the Turtle entry and add it to the graph

    graph.parse(data=turtle_entry, format='turtle')

    # Iterate over each triple in the graph and print the subject, predicate, and object
    for predicate, subject,  obj in graph:
        properties["subject"] = subject
        properties["predicate"] = predicate
        #print(f"subject: {subject}")
        #print(f"Predicate: {predicate}")
        if isinstance(obj, URIRef):
            properties["object"] = obj.n3()
            #print(f"Object: {obj.n3()}")
        elif isinstance(obj, Literal):
            properties["object"] = obj.n3()
            #print(f'Object: "{obj.value}"')
        
        all_the_properties.append(properties)
        properties={}

    return all_the_properties

def sort_dict_by_values(dictionary):
    #print("sort dick")
    keys = []
    values = []
    for key, value in sorted(dictionary.items(), key=lambda item: (item[1], item[0]), reverse=True):
        keys.append(key)
        values.append(value)
    return keys, values

def preprocess_relations(file, prop=False):
    print("preprocess_relations")
    relations = {}
    with open(file, encoding='utf-8') as f:
        content = f.readlines()
        for line in content:
            split_line = line.split()
            #print(split_line)

            key = ' '.join(split_line[2:])[1:-3].lower()
            key = ' '.join([stemmer.stem(word) for word in key.split()])

            if key not in relations:
                relations[key] = []

            uri = split_line[0].replace('<', '').replace('>', '')

            if prop is True:
                uri_property = uri.replace('/ontology/', '/property/')
                relations[key].extend([uri, uri_property])
            else:
                relations[key].append(uri)
    return relations

def get_earl_entities(query):
    #print("earl")
    result = {}
    result['question'] = query
    result['entities'] = []
    result['relations'] = []

    THRESHOLD = 0.1
    #print("do we die")
    #print("This is our query:", query)
    try:
        response = requests.post('http://ltdemos.informatik.uni-hamburg.de/earl/processQuery',
                                json={"nlquery": query, "pagerankflag": False})

        json_response = json.loads(response.text)
        #print(json_response)
        type_list = []
        chunk = []
        for i in json_response['ertypes']:
            type_list.append(i)
        for i in json_response['chunktext']:
            chunk.append([i['surfacestart'], i['surfacelength']])

        keys = list(json_response['rerankedlists'].keys())
        reranked_lists = json_response['rerankedlists']
        for i in range(len(keys)):
            if type_list[i] == 'entity':
                entity = {}
                entity['uris'] = []
                entity['surface'] = chunk[i]
                for r in reranked_lists[keys[i]]:
                    if r[0] > THRESHOLD:
                        uri = {}
                        uri['uri'] = r[1]
                        uri['confidence'] = r[0]
                        entity['uris'].append(uri)
                if entity['uris'] != []:
                    result['entities'].append(entity)
            if type_list[i] == 'relation':
                relation = {}
                relation['uris'] = []
                relation['surface'] = chunk[i]
                for r in reranked_lists[keys[i]]:
                    if r[0] > THRESHOLD:
                        uri = {}
                        uri['uri'] = r[1]
                        uri['confidence'] = r[0]
                        relation['uris'].append(uri)
                if relation['uris'] != []:
                    result['relations'].append(relation)
    except:
        print("earl fail")
    return result

def get_spotlight_entities(query):
    entities = []
    data = {
        'text': query,
        'confidence': '0.2',
        'support': '10'
    }
    headers = {"Accept": "application/json"}
    try:
        response = requests.post('https://api.dbpedia-spotlight.org/en/annotate', data=data, headers=headers)
        response_json = response.text.replace('@', '')
        output = json.loads(response_json)
        #print(output)
        if 'Resources' in output.keys():
            resource = output['Resources']
            for item in resource:
                entity = {}
                uri = {}
                uri['uri'] = item['URI']
                uri['confidence'] = float(item['similarityScore'])
                entity['uris'] = [uri]
                entity['surface'] = [int(item['offset']), len(item['surfaceForm'])]
                entities.append(entity)
    except:
        print('Spotlight: ', query)
    return entities

def get_nliwod_entities(query, hashmap):
    ignore_list = []
    entities = []
    singular_query = [stemmer.stem(word) if p.singular_noun(word) == False else stemmer.stem(p.singular_noun(word)) for word in query.lower().split(' ')]

    string = ' '.join(singular_query)
    words = query.split(' ')
    #print("THIS IS WORDs",words)
    indexlist = {}
    surface = []
    current = 0
    locate = 0
    for i in range(len(singular_query)):
        indexlist[current] = {}
        indexlist[current]['len'] = len(words[i])-1
        indexlist[current]['surface'] = [locate, len(words[i])-1]
        current += len(singular_query[i])+1
        locate += len(words[i])+1
    for key in hashmap.keys():
        #print("THIS IS KEY",key ,"and this is singularQ", singular_query)
        if key in string and len(key) > 2 and key not in ignore_list:
            e_list = list(set(hashmap[key]))
            k_index = string.index(key)
            if k_index in indexlist.keys():
                surface = indexlist[k_index]['surface']
            else:
                for i in indexlist:
                    if k_index>i and k_index<(i+indexlist[i]['len']):
                        surface = indexlist[i]['surface']
                        break
            for e in e_list:
                r_e = {}
                r_e['surface'] = surface
                r_en = {}
                r_en['uri'] = e
                r_en['confidence'] = 0.5
                r_e['uris'] = [r_en]
                entities.append(r_e)
    return entities

def merge_entity(old_e, new_e):
    for new_entity in new_e:
        exist = False
        for already_exist_entites in old_e:
            for item in already_exist_entites['uris']:
                #rint(item['uris'][0]['uri'])
                if new_entity['uris'][0]['uri'] == item['uri']:
                    item['confidence'] = max(item['confidence'], new_entity['uris'][0]['confidence'])
                    exist = True
        if not exist:
            old_e.append(new_entity)
    return old_e

def merge_relation(old_e, new_e):
    for i in range(len(new_e)):
        for j in range(len(old_e)):
            if new_e[i]['surface']==old_e[j]['surface']:
                for i1 in range(len(new_e[i]['uris'])):
                    notexist = True
                    for j1 in range(len(old_e[j]['uris'])):
                        if new_e[i]['uris'][i1]['uri']==old_e[j]['uris'][j1]['uri']:
                            old_e[j]['uris'][j1]['confidence'] = max(old_e[j]['uris'][j1]['confidence'], new_e[i]['uris'][i1]['confidence'])
                            notexist = False
                    if notexist:
                        old_e[j]['uris'].append(new_e[i]['uris'][i1])
    return old_e

def find_indexes(sentence, target_word):
    words = sentence.split()
    #print(target_word)
    index_for_word = 0
    for i in range(len(words)):
        if words[i] == target_word:
            index_for_word = i

    res = [(ele.start(), ele.end() - 1) for ele in re.finditer(r'\S+', sentence)]
    #print(index_for_word)
    return res[index_for_word]

def add_item(item,list,question,word):
    stupid_formating={}
    even_more_stupid_formating=[]
    local = find_indexes(question,word)
    stupid_formating['uri'] = item
    stupid_formating['confidence'] = 0.75
    list['surface'] = local[::-1]
    even_more_stupid_formating.append(stupid_formating)
    list['uris'] = even_more_stupid_formating
    #idk what confidence to give
    
    return list


def spacy_parse(question, properties):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(question)
    entities = []
    relationships = []
    entity={}
    relation = {}
    #print(properties)
    for token in doc:
        for line in properties:
            #print(token.text)
            #checking if the word in the sentence exists within the subject, predicate or object of our knowledge graph
            #the re.search and espace is for the regex expression so e.g "the_dog" is not selected when we look for "the"
            if re.search(r'\b'+re.escape(token.text )+r'\b', line['subject']):
                #print(token.text,line['subject'],"subject")
                if not any(entity['uris'] == token.text for entity in entities):
                    add_item(token.text,entity,question,token.text)
                    entities.append(entity)
                    entity = copy.deepcopy(entity)
                    #entities.append(token.text)
                if not any(relation['uris'] == line['subject'] for relation in relationships):
                    add_item(line['subject'],relation,question,token.text)
                    relationships.append(relation)
                    relation = copy.deepcopy(relation)

            if re.search(r'\b'+re.escape(token.text )+r'\b', line['predicate']):
                #print(token.text,line['predicate'],"predicate")
                
                if not any(relation['uris'] == token.text for relation in relationships):
                    add_item(token.text,relation,question,token.text)
                    relationships.append(relation)
                    relation = copy.deepcopy(relation)

            if re.search(r'\b'+re.escape(token.text )+r'\b', line['object']):
                #print(token.text,line['object'],"object")
                if not any(entity['uris'] == token.text  for entity in entities):
                #if token.text not in entities:
                    entity= add_item(token.text,entity,question,token.text)
                    entities.append(entity)
                    entity = copy.deepcopy(entity)
                
                #print(relationships.keys())
                if not any(relation['uris'] == line['predicate'] for relation in relationships):
                    relation = add_item(line['predicate'],relation,question,token.text)
                    relationships.append(relation)
                    relation = copy.deepcopy(relation)

                    #relationships.append(line['predicate'])
            
            '''f len(entity)> 0 or len(relation)> 0:
                relationships.append(relation)
                entities.append(entity)
                relation = copy.deepcopy(relation)
                entity = copy.deepcopy(entity)'''


    #print("Entities:", entities)
    #print("Relationships:", relationships)
    
    return entities,relationships
    


class PhraseMapping:
    def __init__(self):
        self.properties = []
        self.properties = preprocess_relations('turtle/dbpedia_3Eng_property.ttl', True)
        self.properties_knowledgegraph = preprocess_relations('turtle/knowledge_graph.ttl')
        self.subject_prop_object_ttl = process_knowledge_graph('turtle/knowledge_graph.ttl')
    
        for key in self.properties_knowledgegraph.keys():
            if key in self.properties:
                self.properties[key].extend(self.properties_knowledgegraph[key])
            else:
                self.properties[key] = self.properties_knowledgegraph[key]
        

    def phrasemap_question(self, question,tokened_question):
        phrasemap_data=[]
        print('properties: ', len(self.properties))

        earl = get_earl_entities(question)
        print("This is earl",earl)
        print("#"*20)
        
        nliwod = get_nliwod_entities(question, self.properties)
        print("This is nliwod" ,nliwod)
        print("#"*20)
        if len(nliwod) > 0:
            earl['relations'] = merge_entity(earl['relations'], nliwod)
            
        spot_e = get_spotlight_entities(question)
        print("This is spot_e" ,spot_e)
        print("#"*20)

        if len(spot_e) > 0:
            earl['entities'] = merge_entity(earl['entities'], spot_e)

        #spacy is used to check if the knowledge graph contains relations or entities that the question does. 
        spacy_e, spacy_r= spacy_parse(question,self.subject_prop_object_ttl)
        #print(spacy_e)
        if len(spacy_e) > 0:
            print("THIS IS SPACY ENITIY",spacy_e)
            print("#"*20)
            earl['entities'] = merge_entity(earl['entities'], spacy_e,)
        if len(spacy_r) > 0:
            print("THIS IS SPACY RELATIONS",spacy_r)
            print("#"*20)
            earl['relations'] = merge_entity(earl['relations'], spacy_r)


        esim = []
        for i in earl['entities']:
            i['uris'] = sorted(i['uris'], key=lambda k: k['confidence'], reverse=True)
            esim.append(max([j['confidence'] for j in i['uris']]))

        earl['entities'] = np.array(earl['entities'])
        esim = np.array(esim)
        inds = esim.argsort()[::-1]
        earl['entities'] = earl['entities'][inds]

        rsim = []
        for i in earl['relations']:
            i['uris'] = sorted(i['uris'], key=lambda k: k['confidence'], reverse=True)
            rsim.append(max([j['confidence'] for j in i['uris']]))

        earl['relations'] = np.array(earl['relations'])
        rsim = np.array(rsim)
        inds = rsim.argsort()[::-1]
        earl['relations'] = earl['relations'][inds]

        earl['entities'] = list(earl['entities'])
        earl['relations'] = list(earl['relations'])

        phrasemap_data.append(earl)
        

        #print(get_nliwod_entities(question,self.properties))
        with open('json_files/phrasemapping.json', "w") as data_file:
            json.dump(phrasemap_data, data_file, sort_keys=True, indent=4, separators=(',', ': '))
        
        #is_question_within_knowledge_graph_domain = knowledge_graph_check(tokened_question, self.subject_prop_object_ttl)

        #return is_question_within_knowledge_graph_domain,spacy_r,spacy_e
