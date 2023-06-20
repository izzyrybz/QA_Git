import time
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import requests, json, re, operator
from myclassifier import QuestionClassifier
from myphrasemapping import PhraseMapping

from knowledgegraph_generator import KnowledgeGraphGenerator
from generate_q_rank_q import generate_query
import spacy
from spacy import displacy
from nltk import Tree
import itertools
import string
import difflib


def question_analysis(question):
        # Parse the input text using spaCy
        nlp = spacy.load("en_core_web_sm")
        question = nlp(question)

        #find the lemmas, the tokens and 
        representation = question_representation(question)

        #get the question as the most grammatical basic form
        lemmizized_question =""
        for line in representation:
            lemmizized_question+= (line[1]+" ")
        
        #print(lemmizized_question)
        lemmizized_question = nlp(lemmizized_question)
        
        #use this information to generate a dependency tree
        dependecy_tree = dependecy_tree_generation(lemmizized_question)
        return dependecy_tree,lemmizized_question,representation

def question_representation(question):
     # Mapping to a Machine-Readable representation
    representation = []
    for token in question:
        representation.append((token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.ent_type_))
        #print("this is the lemma",token.lemma_ ,"and tag", token.tag_, "and entity type" ,token.ent_type_, "for the word", token.text)
    return representation

def dependecy_tree_generation(question):
    dep_tree = []
    for token in question:
        dep_tree.append({
            "text": token.text,
            "head": token.head.text,
            "dep": token.dep_,
            "pos": token.pos_
        })
    #displacy.serve(question, style="dep", options={"compact": True})
    
    return dep_tree

def prepare_data(question_type):
     
    entity_uris = []
    relations_uris = []
    with open('json_files/phrasemapping.json','r') as fp:
        phrasemap = json.load(fp)

    for item in phrasemap:
        entities = item['entities']
        relations = item['relations']

    for entity_uri in entities:
        entity_uris.append(entity_uri['uris'][0])

    for relations_uri in relations:
        relations_uris.append(relations_uri['uris'][0])
    
    if question_type == 'count':
        question_type = 2
    
    if question_type == 'boolean':
        question_type = 1
    
    else:
        question_type = 0

    return entity_uris, relations_uris, question_type

def build_query(query_params, question_type):
    query = query_params["query"]

    #remove the SELECT * WHERE
    query = re.sub(r'^SELECT\s*\*\s*WHERE\s*{\s*', '', query)
    
    #or 
    query = re.sub(r'\bASK WHERE\b', '', query)
    if query[-1] == '}':
        query=query[:-1]
    #print("this is query",query)

    for item in query.split():
        if item.startswith('?'):
            target_var =item
            
    

    if question_type[0] == 'count':
        where_clause = "SELECT COUNT (DISTINCT "+target_var+") WHERE {"
    
    elif question_type[0] == 'boolean':
        where_clause = "ASK WHERE "
    
    else:
        where_clause = "SELECT DISTINCT "+target_var+" WHERE {"
    
    sparlq_query = where_clause +  query + "}"
    return sparlq_query
    #print(sparlq_query)


#if __name__ == "__main__":
def main(question,phrasemapper):
    # Load the spaCy model
    

    print("Question:" ,question)

    #Parse the input question using spaCy and then create representation and dependency tree
    #returns depency tree and lemmeized question and the question tokenized (verbs,nouns ect)
    dependecy_tree,lemmizized_question,tokened_question = question_analysis(question)

    print("Lemma",lemmizized_question)
    print("Dependency Tree: " ,dependecy_tree)
    print("Tokenized question:" ,tokened_question)

    #create an instance of a classifier that looks at the questions and returns what type the question is
    classifier = QuestionClassifier()
    question_type = classifier.classify_questions(question)
    print("Type of question:",question_type)
    print("#"*80)

    #We create a phrase mapping
    phrasemapper.phrasemap_question(question,tokened_question,lemmizized_question)
    print("phrasemapping generated in file that can be found under json_files")
    print("#"*80)
    


   #prepare the data for the question_generator
    entites,relations,num_question_type = prepare_data(question_type)
    h1_threshold=999999

    #the file for generate_query contains ranking too
    query_generator = generate_query(question,entites,relations,h1_threshold,num_question_type)
    print("the query ranked highest and most probable:", query_generator)
    print("#"*80)

    finished_query = build_query(query_generator,question_type)
    #print("finished query",finished_query)
    #return str(finished_query)
    
    return finished_query

    jena_response = requests.get("http://localhost:3030/dbpedia/query", params={"query": finished_query})
    if jena_response.status_code == 200:
            results = jena_response.json()
            output = results["results"]["bindings"]
            #print("The answer is",output)
    


phrasemapper = PhraseMapping()

with open('testingdata.txt','r') as fp:
    for line in fp:
            print(main(line,phrasemapper))
print("We have finished the questions")
