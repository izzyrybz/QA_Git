import spacy
from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Span

import sys
import requests
from nltk.stem.porter import *
import nltk
from nltk import word_tokenize, pos_tag, ne_chunk
import json
import networkx as nx


def ttl_file_processing(filepath):
    graph = Graph()
    all_the_properties=[]
    properties={}

    with open(filepath, 'r') as file:
        turtle_entry = file.read()
# Parse the Turtle entry and add it to the graph

    graph.parse(data=turtle_entry, format='turtle')

    # Iterate over each triple in the graph and print the subject, predicate, and object
    for subject, predicate, obj in graph:
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


# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Define the object, predicate, and subject
dbpedia_c = ttl_file_processing('turtle/dbpedia_3Eng_class.ttl')
dbpedia_p= ttl_file_processing('turtle/dbpedia_3Eng_property.ttl')
knowledge_graph_p= ttl_file_processing('turtle/knowledge_graph.ttl')
print(dbpedia_p)
      
for text in knowledge_graph_p:

    # Define the input sentence
    text = f"{subject} {predicate} {object}"

    # Create a spaCy doc from the input sentence
    doc = nlp(text)

    # Define a spaCy Matcher to find the object, predicate, and subject in the sentence
    matcher = Matcher(nlp.vocab)
    matcher.add("OBJECT_PREDICATE_SUBJECT", None, [{"LOWER": object.lower()}, {"LOWER": predicate.lower()}, {"LOWER": subject.lower()}])

    # Define a spaCy PhraseMatcher to map the matched phrase to a new concept
    phrase_matcher = PhraseMatcher(nlp.vocab)
    phrase_matcher.add("PIZZA_LOVER", None, nlp("pizza lover"))

    # Use the Matcher to find the object, predicate, and subject in the sentence
    matches = matcher(doc)

    # If there is at least one match, use the PhraseMatcher to map the matched phrase to a new concept
    if len(matches) > 0:
        match_id, start, end = matches[0]
        span = Span(doc, start, end)
        phrase_match = phrase_matcher(doc[start:end])
        if len(phrase_match) > 0:
            for match_id, start, end in phrase_match:
                matched_span = Span(doc, start, end, label=match_id)
                doc.ents = list(doc.ents) + [matched_span]

    # Print the entities in the doc
    for ent in doc.ents:
        print(ent.text, ent.label_)