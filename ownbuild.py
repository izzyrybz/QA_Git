from SPARQLWrapper import SPARQLWrapper, JSON
import json
import requests, json, re, operator
from myclassifier import QuestionClassifier
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

    
##################################### LCQUAD BENCHMARK ##########################################3
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    correct_count = 0
    correct_count_question = []
    count_q_question = []
    count_q = 0
    
    #for question in data["corrected_question"]:
    for question in data:
        #print(question["corrected_question"])
        dependecyTree,lemmizized_question = question_analysis(question["corrected_question"])
        #questions_type = question_type_classifcation(lemmizized_question)
        #print(questions_type)
        classifier = QuestionClassifier()
        question_type = classifier.classify_questions(question["corrected_question"])
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

        

      
################################ ONE SINGLE QUESTION ###########################################
'''
# Define the input question
    question = "Count everyone who studied at an institute which are in Suburbs?"

# Alternative questions
# How many commits have the user izzyrybz made?
# Who is the mayor of the capital of French Polynesia?
# When was the initial commit created?
# How many merges have there been?
# When was world war 2?
# What language is the repository written in?
# Who is the wife of Obama?

#What is the total number of other tenant of the stadia whose one of the tenant is Raptors 905?
#Count everyone who studied at an institute which are in Suburbs?
#Count the units garrisoned at Arlington County, Virginia.
#Count the number of sports team members  which have player named Matt Williams ?

# Did world war 2 happen?
# Is Isabelle Rybank in office?
# Can Sebastian mountain climb?
# What year was Cristiano Ronaldo born?
# When did the queen earn the throne?

#### WHEN DID - BOOLEAN - NOT GOOD / TOO MANY LISTS

    dependecyTree,lemmizized_question = question_analysis(question)
    #questions_type = question_type_classifcation(lemmizized_question)
    #print(lemmizized_question)
    classifier = QuestionClassifier()
    question_type = classifier.classify_questions(question)
    print(question_type)



#     #question = input("Write question")'''


    # Parse the input question using spaCy and then create representation and dependency tree
    #returns depency tree and lemmeized question
'''dependecyTree,lemmizized_question = question_analysis(question)
    questions_type = question_type_classifcation(lemmizized_question)
    print(questions_type)'''


   

    
    #displacy.serve(doc, style="dep", options={"compact": True})

    
    #print(lemmas) 
    #print(build_sparql_query(dep_tree))

