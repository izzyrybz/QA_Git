import itertools
import json

from rdflib import Graph

from myphrasemapping import process_knowledge_graph

def generate_combinations(predicate,subj,obj):
        #print(self.relationship_uris)
        #print(self.entity_uris)
        # Generate all possible combinations of entities and relationships
        combination_indexes = itertools.product(predicate,subj,obj)
        for tup in combination_indexes:
            print(tup)

        '''entity_combinations = itertools.combinations(range(len(self.entity_uris)), 3)
        relationship_combinations = itertools.permutations(range(len(self.relationship_uris)), 3)

        combinations = []

        # Loop through each combination and generate the options
        for e_firstindex,e_secondindex  in entity_combinations:
            for r_firstindex,r_secondindex in relationship_combinations:
                print("PRINT",self.entity_uris[e_firstindex])
                # Construct the query string
                query = f"SELECT ?{self.entity_uris[e_firstindex]} ?{self.entity_uris[e_secondindex]} WHERE ?{self.entity_uris[e_firstindex]} {self.relationship_uris[r_firstindex]} ?{self.entity_uris[e_secondindex]} . ?{self.entity_uris[e_firstindex]} {self.relationship_uris[r_secondindex]} ?{self.entity_uris[e_secondindex]} . "

                # Add the relevant question tokens to the query
                
                # Add the closing braces to the query
                query += "}"
                #print(query)  

                # Add the query to the list of queries
                combinations.append(query)
                '''

def get_entity_relation_from_graph(knowledge_graph_info, entites, relations):
    #print("in get entity and relation from knowledge_graph_info")
    graph_entities = []
    for entity in entites:
        #print(entity)
        for item in knowledge_graph_info:
            for uri in item.values():
               if entity in uri:
                    #print("does this work")
                    #unsure if this should be extended with the item since that shows the full relationship????
                    if entity not in graph_entities:
                        graph_entities.append(entity)
            

            #if entity in item:
    #print(graph_entities)

    graph_relation = []
    for relation in relations:
        #print(relation)
        for item in knowledge_graph_info:
            for uri in item.values():
               if relation in uri:
                    #print("does this work")
                    #unsure if this should be extended with the item since that shows the full relationship????
                    if relation not in graph_relation:
                        graph_relation.append(relation)
            


    return graph_entities,graph_relation
            

            #if entity in item:

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
            #print("we have a list")
            where_clause = 'SELECT DISTINCT'
        elif(question_type[0] == 'count'):
            where_clause = 'SELECT COUNT'
        elif(question_type[0] == 'boolean'):
                    where_clause = 'ASK WHERE {'

        ####### GOING AFTER THE ALGO IN THE PAPER #####

        #Step 1: find out what entities and properties that are part of the knowledge graph to generate the sets

        graph_entities,graph_relation = get_entity_relation_from_graph(self.knowledge_graph_info, self.entity_uris, self.relationship_uris)
        print("this is the entities can be found in the knowledge graph: ",graph_entities)
        print("this is the relation can be found in the knowledge graph: ",graph_relation)

        #Generate all the possible combinations of the entites, realtion and uri
        set1_e_p_e = set(itertools.product(graph_entities,graph_relation,graph_entities))
        set2_e_p_uri = set(itertools.product(graph_entities,graph_relation,['?uri']))
        set2_uri_p_e = set(itertools.product(['?uri'],graph_relation,graph_entities))

        all_sets = set1_e_p_e|set2_e_p_uri|set2_uri_p_e
        #for tup in all_sets:
        #    print(tup)

        # I think the next step is now to check if this combination exists in the knowledge graph
        # i.e ('http://dbpedia.org/resource/Commit_(version_control)', 'https://dbpedia.org/ontology/author', '?uri') no
        # '?uri', 'https://dbpedia.org/ontology/author', 'izzyrybz' YES

    

       

                
        #with open('json_files/dmump.json', "w") as data_file:
        #            json.dump(queries, data_file, sort_keys=True, indent=4, separators=(',', ': '))
        

