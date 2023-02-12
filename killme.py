from SPARQLWrapper import SPARQLWrapper, JSON

import spacy
from spacy import displacy


nlp = spacy.load("en_core_web_sm")

'''def build_sparql_query(dep_tree):
    query = "SELECT ?repo ?property ?value WHERE {\n"
    for token in dep_tree:
        if token["dep"] in ["nsubj", "attr"]:
            repo = token["head"].capitalize()
            property = token["text"].capitalize().replace(" ", "_")
            value = "?value"
            query += f"\t?repo {property} {value} .\n"
    query += "}"
    return query

def generate_sparql_query(question):
    doc = nlp(question)
    dep_tree = []
    for token in doc:
        dep_tree.append({
            "text": token.text,
            "head": token.head.text,
            "dep": token.dep_,
            "pos": token.pos_
        })
    return build_sparql_query(dep_tree)

question = "What is the language of the repository named Git-Tutorial?"

print(generate_sparql_query(question))'''


def build_sparql_query(dep_tree):
    query = "SELECT ?subject ?predicate ?object WHERE {\n"
    for token in dep_tree:
        if token["dep"] in ["nsubj", "dobj"]:
            print(token)
            subject = token["text"].capitalize()
            predicate = token["text"].capitalize().replace(" ", "_")
            object = token["head"].capitalize()
            query += f"\t?subject {predicate} ?object .\n"
    query += "}"
    return query

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Define the input text
text = "How many commits has the author izzyrybz made?"
#text = input("Write question")


# Parse the input text using spaCy

doc = nlp(text)
#lemmas = [token.lemma_ for token in doc]


# Mapping to a Machine-Readable Representation
representation = []
for token in doc:
    representation.append((token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.ent_type_))

# Print the representation
print(representation)

#displacy.serve(doc, style="dep", options={"compact": True})

dep_tree = []
for token in doc:
    dep_tree.append({
        "text": token.text,
        "head": token.head.text,
        "dep": token.dep_,
        "pos": token.pos_
    })
print(dep_tree)
#print(lemmas) 
print(build_sparql_query(dep_tree))



'''# Connect to the reference dataset
sparql = SPARQLWrapper("http://localhost:3030/#/dataset/test4commits/query")

# Define the query
query = """
SELECT ?object
WHERE {
	
<http://example.org/65970ecb019eef5a3b2f709180113213e6000a78>
  <http://example.com/author>
   ?object
}
"""
sparql.setQuery(query)
sparql.setReturnFormat(JSON)

# Execute the query and retrieve the results
results = sparql.query().convert()

# Store the results in a list
#golden_standard = []
#for result in results["results"]["bindings"]:
#    person = result["author"]["value"]
#    golden_standard.append((person))

# Print the golden standard
print(results)'''



'''import requests
question = input("What is your question?")

#question = "Barack Obama was the 44th President of the United States."

url = "http://api.dbpedia-spotlight.org/en/annotate"

headers = {
    "Accept": "application/json"
}

payload = {
    "text": question,
    "confidence": 0.25,
    "support": 20
}

response = requests.get(url, headers=headers, params=payload)

if response.status_code == 200:
    entities = response.json()["Resources"]
    for entity in entities:
        print(entity["@URI"])
else:
    print("Annotation request failed.")'''
