from SPARQLWrapper import SPARQLWrapper, JSON
import json
import requests, json, re, operator

import spacy
from spacy import displacy
from nltk import Tree

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
        dependecyTree = dependecy_tree(lemmizized_question)
        return dependecyTree,lemmizized_question


def question_representation(question):
    
    #doc = nlp(question)

    # Mapping to a Machine-Readable representation
    representation = []
    for token in question:
        representation.append((token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.ent_type_))
        #print("this is the lemma",token.lemma_ ,"and tag", token.tag_, "and entity type" ,token.ent_type_, "for the word", token.text)
    
    return representation

def dependecy_tree(question):
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


def question_type_classifcation(question):
    #print(question)
    question_word = [token.text for token in question if token.dep_ == "ROOT"][0]
    if question_word.lower() in ["how", "what", "which"]:
        if any([token.text.lower() in ["many", "much"] for token in question]):
            return "count"
        else:
            return "list"
    elif question_word.lower() in ["is", "are", "was", "were", "do", "does", "did", "be"]:
        return "boolean"
    else:
        return "unknown"


def build_sparql_query(dep_tree):
    query = "SELECT ?subject ?predicate ?object WHERE {\n"
    for token in dep_tree:
        if token["dep"] in ["nsubj", "dobj"]:
            print(token)
            subject = token["question"].capitalize()
            predicate = token["question"].capitalize().replace(" ", "_")
            object = token["head"].capitalize()
            query += f"\t?subject {predicate} ?object .\n"
    query += "}"
    return query

    

if __name__ == "__main__":
    # Load the spaCy model
    nlp = spacy.load("en_core_web_sm")

    #trying with the benchmark from qa-code

    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    #for question in data["corrected_question"]:
    for question in data:
        #print(question["corrected_question"])
        dependecyTree,lemmizized_question = question_analysis(question["corrected_question"])
        questions_type = question_type_classifcation(lemmizized_question)
        print(questions_type)
        

      


    

    # Define the input question
    #question = "Is Isabelle Rybank in office?"

# Alternative questions
# How many commits have the user izzyrybz made?
# Who is the mayor of the capital of French Polynesia?
# When was the initial commit created?
# How many merges have there been?
# What language is the repository written in?
# Who is the wife of Obama?
# Is Isabelle Rybank in office?

#     #question = input("Write question")


    # Parse the input question using spaCy and then create representation and dependency tree
    #returns depency tree and lemmeized question
    '''dependecyTree,lemmizized_question = question_analysis(question)
    questions_type = question_type_classifcation(lemmizized_question)
    print(questions_type)'''


   

    
    #displacy.serve(doc, style="dep", options={"compact": True})

    
    #print(lemmas) 
    #print(build_sparql_query(dep_tree))

