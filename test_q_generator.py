import itertools
import json

from rdflib import Graph

from myphrasemapping import process_knowledge_graph

def generate_combinations():
        #print(self.relationship_uris)
        #print(self.entity_uris)
        # Generate all possible combinations of entities and relationships
        entity_combinations = itertools.combinations(range(len(self.entity_uris)), 2)
        relationship_combinations = itertools.permutations(range(len(self.relationship_uris)), 2)

        combinations = []

        # Loop through each combination and generate the options
        for e_firstindex,e_secondindex  in entity_combinations:
            for r_firstindex,r_secondindex in relationship_combinations:
                print("PRINT",self.entity_uris[e_firstindex])
                # Construct the query string
                query = f"SELECT ?{self.entity_uris[e_firstindex]} ?{self.entity_uris[e_secondindex]} WHERE ?{self.entity_uris[e_firstindex]} {self.relationship_uris[r_firstindex]} ?{self.entity_uris[e_secondindex]} . ?{self.entity_uris[e_firstindex]} {self.relationship_uris[r_secondindex]} ?{self.entity_uris[e_secondindex]} . "

                # Add the relevant question tokens to the query
                '''for token in question_tokens:
                    if token in entity_combo or token in relationship_combo:
                        continue
                    else:
                        query += f"?{entity_combo[0]} <{token}> ?{token} . ?{entity_combo[1]} <{token}> ?{token} . "'''

                # Add the closing braces to the query
                query += "}"
                #print(query)  

                # Add the query to the list of queries
                combinations.append(query)

def get_entity_relation_from_KG(knowledge_graph_info, entites, relations):
    for item in knowledge_graph_info:
        print(item)

class QuestionGenerator():
    def __init__(self):
        with open('json_files/phrasemapping.json','r') as fp:
            self.data = json.load(fp)

        #print(data)
        self.entity_uris =[]
        self.relationship_uris = []
        # Get the uris from entites and relations from the phrasemapping
        #print(data)
        
        for entity_data in self.data:
            for entity in entity_data["entities"]:
                for uris in entity['uris']:
                    #print(uris['uri'])
                    self.entity_uris.append(uris['uri'])
        
        for relationship_data in self.data:
            for relations in relationship_data["relations"]:
                for uris in relations['uris']:
                    #print(uris['uri'])
                    self.relationship_uris.append(uris['uri'])
        
        self.knowledge_graph_info = process_knowledge_graph('turtle/knowledge_graph.ttl')



 
    def generate_sparql_queries(self,question_type, question_tokens):
        #check type and corresponding where clause
        if(question_type[0] == 'list'):
            print("we have a list")
            where_clause = 'SELECT DISTINCT'
        elif(question_type[0] == 'count'):
            where_clause = 'SELECT COUNT'
        elif(question_type[0] == 'boolean'):
                    where_clause = 'ASK WHERE {'

        print(self.relationship_uris)
        #graph = Graph()

        ####### GOING AFTER THE ALGO IN PAPER #####

        #Step 1: find out what entities and properties that are part of the knowledge graph to generate the sets
        #knowledge graph = KG

        list = get_entity_relation_from_KG(self.knowledge_graph_info, self.entity_uris, self.relationship_uris)
        

        
        set1_e_p_e = {}


        set2_e_p_uri = {}
        set2_uri_p_e = {}
        #the idea is also to check if the question is within the knowledge graph, which has been done by previous method
        #use this information to check which of the entites and relations are in the knowledge graph

       

                
        #with open('json_files/dmump.json', "w") as data_file:
        #            json.dump(queries, data_file, sort_keys=True, indent=4, separators=(',', ': '))
        

