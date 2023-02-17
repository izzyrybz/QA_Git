
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
p = inflect.engine()
tagme.GCUBE_TOKEN = ""

import rdflib

def ttl_file_processing(filepath):
    rdf_type_pattern = re.compile(r'<.+> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <(.+)> .')

    # Define the regular expression pattern for matching RDF labels
    rdf_label_pattern = re.compile(r'<(.+)> <http://www.w3.org/2000/01/rdf-schema#label> "(.+)" .')

    # Read in the RDF data from the file
    with open(filepath, 'r') as file:
        rdf_data = file.read()
        print(rdf_data)

    # Find all RDF types and labels in the data
    rdf_types = rdf_type_pattern.findall(rdf_data)
    rdf_labels = rdf_label_pattern.findall(rdf_data)

    # Create a phrasemap dictionary from the RDF labels
    phrasemap = {}
    for rdf_type in rdf_types:
        for rdf_label in rdf_labels:
            if rdf_type == rdf_label[0]:
                phrasemap[rdf_label[1].lower()] = [rdf_type]

    # Print the resulting phrasemap
    print(phrasemap)

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
        print("earl might be done")
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
        print(output)
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
    print("THIS IS WORDs",words)
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
    for i in new_e:
        exist = False
        for j in old_e:
            for k in j['uris']:
                if i['uris'][0]['uri'] == k['uri']:
                    k['confidence'] = max(k['confidence'], i['uris'][0]['confidence'])
                    exist = True
        if not exist:
            old_e.append(i)
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

def nltk_parse(question):
    entity_list= []
    # Tokenize the text
    tokens = word_tokenize(question)
    # Perform part-of-speech tagging
    tagged = pos_tag(tokens)
    # Perform Named Entity Recognition
    entities = ne_chunk(tagged)
    # Iterate over the entities and print the entity text and label
    for entity in entities:
        #print(entity)
        if hasattr(entity, 'label'):
            entity_list.append(entity)
    return entity_list

def spacy_parse(question,tokened_question, properties):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(question)
    entities = []
    relationships = []
    '''for token in doc:
        #print(properties.keys())
        for keywords in properties.keys():
            if token.text.lower() in keywords:
                entities.append((token.text, keywords))
            if token.text.lower() == keywords[0]:
                for child in token.children:
                    for rel, rel_keywords in properties.keys():
                        if child.text.lower() in rel_keywords:
                            relationships.append((keywords, rel))
                            doc = nlp(question)'''
    entities = []
    relationships = []
    #print(properties)
    for token in doc:
        for key, values in properties.items():
            for value in values:
                #print(value)
                if value.lower() in token.text.lower():
                    entities.append((token.text, value, token.prob))
                    break
            if key.lower() in token.text.lower():
                for child in token.children:
                    for value in values:
                        if value != values[0]:
                            if value.lower() in child.text.lower():
                                relationships.append((values[0], value, child.prob))
                                break

    
    return entities,relationships
    


class PhraseMapping:
    def __init__(self):
        self.properties = []
        self.properties = preprocess_relations('turtle/dbpedia_3Eng_property.ttl', True)
        properties_class = preprocess_relations('turtle/dbpedia_3Eng_class.ttl', True)
        properties_knowledgegraph = preprocess_relations('turtle/knowledge_graph.ttl')
    
        #print(properties_knowledgegraph)
        for key in properties_knowledgegraph.keys():
            if key in self.properties:
                self.properties[key].extend(properties_knowledgegraph[key])
            else:
                self.properties[key] = properties_knowledgegraph[key]
        
        
        #print(properties)

    def phrasemap_question(self, question,tokened_question):
        phrasemap_data=[]
        print('properties: ', len(self.properties))

        #how to start the phrasemapping
        earl = get_earl_entities(question)
        print("This is earl",earl)
        
        '''nltk = nltk_parse(question)
        print("this is nltk" ,nltk_parse(question))
        if len(nltk) > 0:
            earl['relations'] = merge_entity(earl['relations'], nltk)'''

       
        
        nliwod = get_nliwod_entities(question, self.properties)
        #print("This is nliwod" ,nliwod)
        if len(nliwod) > 0:
            earl['relations'] = merge_entity(earl['relations'], nliwod)
            
        spot_e = get_spotlight_entities(question)
        print("This is spot_e" ,spot_e)

        if len(spot_e) > 0:
            earl['entities'] = merge_entity(earl['entities'], spot_e)

        '''spacy= spacy_parse(question,tokened_question,self.properties)
        print(spacy)
        if len(spacy) > 0:
            earl['entities'] = merge_entity(earl['entities'], spacy[0])
        if len(spacy) > 0:
            earl['relations'] = merge_entity(earl['relations'], spacy[1])'''


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
        print(question)
