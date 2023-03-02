from SPARQLWrapper import SPARQLWrapper, JSON
import json
import requests, json, re, operator
from myclassifier import QuestionClassifier
from myphrasemapping import PhraseMapping
from test_q_generator import QuestionGenerator
from knowledgegraph_generator import KnowledgeGraphGenerator
from killme import generate_query
import spacy
from spacy import displacy
from nltk import Tree
import itertools
import string


def question_analysis(question):
        # Parse the input text using spaCy
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


if __name__ == "__main__":
    # Load the spaCy model
    nlp = spacy.load("en_core_web_sm")
    
##################################### LCQUAD BENCHMARK ##########################################3
    '''
    with open('json_files/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    correct_count = 0
    correct_count_question = []
    count_q_question = []
    count_q = 0
    
    #for question in data["corrected_question"]:
    for question in data:
        print(question["corrected_question"])
        dependecy_tree,lemmizized_question,tokened_question = question_analysis(question["corrected_question"])
        #print(questions_type)
        classifier = QuestionClassifier()
        question_type = classifier.classify_questions(question["corrected_question"])

        phrasemapper = PhraseMapping()
        phrasemapper.phrasemap_question(question["corrected_question"],tokened_question)
        ### Check if count question is correct ##
        print(question_type[0].upper())
        if(question_type[0].upper() in question["sparql_query"]):
            correct_count_question.append(question["corrected_question"])
            correct_count+=1
        if("COUNT" in question["sparql_query"]):
            count_q_question.append(question["corrected_question"])
            count_q +=1
    
    print("result of count question, total", count_q, "correct:", correct_count)
    for question in count_q_question:
        if question in correct_count_question:
            continue
        else:
            print(question)

        
    '''
      
################################ ONE SINGLE QUESTION ###########################################

# Define the input question
    question = "Which commits have the user izzyrybz made?"

#Main focus : Which commits have the user izzyrybz made?

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

    #Knowledge Graph generator to a ttl file that we can use a properties
    KnowledgeGraphGenerator()
    print("Knowledge graph generated")

    #We create a phrase mapping
    phrasemapper = PhraseMapping()
    phrasemapper.phrasemap_question(question,tokened_question)
    print("phrasemapping generated in file that can be found under json_files")



   #prepare the data for the question_generator
    entites,relations,num_question_type = prepare_data(question_type)
    h1_threshold=999999

    question_generator = generate_query(question,entites,relations,h1_threshold,num_question_type)
    

    #generate all possible queries and check if they are within the knowledgegraph
    #question_generator = QuestionGenerator()
    #queries = question_generator.generate_sparql_queries(question_type,tokened_question)



    
    #displacy.serve(doc, style="dep", options={"compact": True})

    
    #print(lemmas) 
    #print(build_sparql_query(dep_tree))

