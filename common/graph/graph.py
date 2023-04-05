from contextlib import closing
import requests
from common.graph.node import Node
from common.graph.edge import Edge
from common.container.uri import Uri
from common.container.linkeditem import LinkedItem
from common.utility.mylist import MyList
import itertools
import logging
from multiprocessing import Pool
from tqdm import tqdm
from urllib.parse import urlparse


class Graph:
    def __init__(self, ):
        self.nodes, self.edges = set(), set()
        self.entity_items, self.relation_items = [], []
        self.suggest_retrieve_id = 0

    def is_uri(self,string):
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
    
    def is_var(self,string):
        if string[0] == '?':
            return True
        else:
            return False

    def is_entity_hash(self,entity):
        if entity in 'http://example.org/entity/hash':
            return True
        else:
            return False
    def create_or_get_node(self, uris, mergable=False):
        if isinstance(uris, (int)):
            uris = self.__get_generic_uri(uris, 0)
            mergable = True
        #print("create_or_get_node",uris)
        new_node = Node(uris, mergable)
        #print("past node ", new_node)
        for node in self.nodes:
            if node == new_node:
                return node
        return new_node

    def add_node(self, node):
        if node not in self.nodes:
            self.nodes.add(node)

    def remove_node(self, node):
        self.nodes.remove(node)

    def add_edge(self, edge):
        if edge not in self.edges:
            self.add_node(edge.source_node)
            self.add_node(edge.dest_node)
            self.edges.add(edge)

    def remove_edge(self, edge):
        edge.prepare_remove()
        self.edges.remove(edge)
        if edge.source_node.is_disconnected():
            self.remove_node(edge.source_node)
        if edge.dest_node.is_disconnected():
            self.remove_node(edge.dest_node)

    def count_combinations(self, entity_items, relation_items, number_of_entities):
        total = 0
        uri_count=0
        for relation_item in relation_items:
            uri_count = uri_count +1 
            for entity_uris in itertools.product(*[items for items in entity_items]):
                total += uri_count * len(list(itertools.combinations(entity_uris, number_of_entities)))
        

        return total
           
    def create_all_combinations(self,entites, relations,num_of_relation):
        all_entites =[]
        all_relations=[]
        hash_entities=[]
        
        #print(entites)
        if len(entites)<1:
            all_entites.append('?u_0')
        else:
            for entity in entites:
                if isinstance(entity, dict):
                    all_entites.append(entity['uri'])
                elif self.is_uri(entity) or self.is_var(entity):
                    all_entites.append(entity)

        if len(relations)<1:
            all_relations.append('?u_0')
        else:
            for relation in relations:
                if isinstance(relation, dict):
                    all_relations.append(relation['uri'])
                elif self.is_uri(relation) or self.is_var(relation):
                    all_relations.append(relation)
        
        #print(all_entites)
        #print(all_relations)
        for entity in all_entites:
            if self.is_entity_hash(entity):
                hash_entities.append(entity)

        if(num_of_relation == '1'):
            ############################# ?u1 ###################################
            set1_s_p_o = set(itertools.product(hash_entities, all_relations, all_entites))
            set2_s_p_u1 = set(itertools.product(hash_entities, all_relations, ['?u_1']))
            set3_s_u1_o = set(itertools.product(hash_entities, ['?u_1'], all_entites))
            set4_u1_p_o = set(itertools.product(['?u_1'], all_relations, all_entites))

            ############################# ?u2 ###################################
            set2_s_p_u2 = set(itertools.product(hash_entities, all_relations, ['?u_0']))
            set3_s_u2_o = set(itertools.product(hash_entities, ['?u_0'], all_entites))
            set4_u2_p_o = set(itertools.product(['?u_0'], all_relations, all_entites))

            ###################### ?u1 and ?u2###############################
            set1_u1_p_u2 = set(itertools.product(['?u_1'], all_relations, ['?u_0']))
            set2_u2_p_u1 = set(itertools.product(['?u_0'], all_relations, ['?u_1']))

            set1_s_u1_u2 = set(itertools.product(hash_entities, ['?u_1'], ['?u_0']))
            set2_s_u2_u1 = set(itertools.product(hash_entities, ['?u_0'], ['?u_1']))
            set_u1 = set1_s_p_o | set2_s_p_u1 | set3_s_u1_o | set4_u1_p_o
            set_u2 = set2_s_p_u2|set3_s_u2_o|set4_u2_p_o
            set_s_p_o_u1_u2 =  set1_u1_p_u2 | set2_u2_p_u1 | set1_s_u1_u2 | set2_s_u2_u1
            all_sets = set_u1|set_u2|set_s_p_o_u1_u2
        

        elif(num_of_relation == '3'):
            ############################# ?u1 ###################################
            set1_s_p_o = set(itertools.product(hash_entities, all_relations, all_entites))
            set2_s_p_u1 = set(itertools.product(hash_entities, all_relations, ['?u_1']))
            set3_s_u1_o = set(itertools.product(hash_entities, ['?u_1'], all_entites))
            set4_u1_p_o = set(itertools.product(['?u_1'], all_relations, all_entites))

            ############################# ?u2 ###################################
            set2_s_p_u2 = set(itertools.product(hash_entities, all_relations, ['?u_0']))
            set3_s_u2_o = set(itertools.product(hash_entities, ['?u_0'], all_entites))
            set4_u2_p_o = set(itertools.product(['?u_0'], all_relations, all_entites))

            ############################## ?u3##############################
            set2_s_p_u3 = set(itertools.product(hash_entities, all_relations, ['?u_3']))
            set3_s_u3_o = set(itertools.product(hash_entities, ['?u_3'], all_entites))
            set4_u3_p_o = set(itertools.product(['?u_3'], all_relations, all_entites))
        

                ###################### ?u1 and ?u2###############################
            set1_u1_p_u2 = set(itertools.product(['?u_1'], all_relations, ['?u_0']))
            set2_u2_p_u1 = set(itertools.product(['?u_0'], all_relations, ['?u_1']))

            set1_s_u1_u2 = set(itertools.product(hash_entities, ['?u_1'], ['?u_0']))
            set2_s_u2_u1 = set(itertools.product(hash_entities, ['?u_0'], ['?u_1']))

            ###########################?u1 and ?u3#################################
            set1_u1_p_u3 = set(itertools.product(['?u_1'], all_relations, ['?u_3']))
            set2_u3_p_u1 = set(itertools.product(['?u_3'], all_relations, ['?u_1']))

            set1_s_u1_u3 = set(itertools.product(hash_entities, ['?u_1'], ['?u_3']))
            set2_s_u3_u1 = set(itertools.product(hash_entities, ['?u_3'], ['?u_1']))

            ######################?u2 and ?u3##################################

            set1_u3_p_u2 = set(itertools.product(['?u_3'], all_relations, ['?u_0']))
            set2_u2_p_u3 = set(itertools.product(['?u_0'], all_relations, ['?u_3']))

            set1_s_u3_u2 = set(itertools.product(hash_entities, ['?u_3'], ['?u_0']))
            set2_s_u2_u3 = set(itertools.product(hash_entities, ['?u_0'], ['?u_3']))

            
            set_u1 = set1_s_p_o | set2_s_p_u1 | set3_s_u1_o | set4_u1_p_o
            set_u2 = set2_s_p_u2|set3_s_u2_o|set4_u2_p_o
            set_u3 = set2_s_p_u3|set3_s_u3_o|set4_u3_p_o
            set_s_p_o_u1_u2 =  set1_u1_p_u2 | set2_u2_p_u1 | set1_s_u1_u2 | set2_s_u2_u1 
            set_s_p_o_u1_u3 =  set1_u1_p_u3 | set2_u3_p_u1 | set1_s_u1_u3 | set2_s_u3_u1 
            set_s_p_o_u2_u3 =  set1_u3_p_u2 | set2_u2_p_u3 |set1_s_u3_u2 | set2_s_u2_u3 

            all_sets = set_u1 |set_s_p_o_u1_u2|set_u2|set_u3|set_s_p_o_u1_u3 | set_s_p_o_u2_u3


        unique_set = set()
        for tup in all_sets:
            if all(tup.count(item) == 1 for item in tup):
                unique_set.add(tup)
        all_sets = unique_set
        with open('allcombi.txt','w') as fp:
            for sets in all_sets:
                for tup in sets:
                    fp.write(str(tup))
                    fp.write(' ')
                fp.write('\n')

        return all_sets
    
    def jena_formatting(self,item):
        
        if item.startswith("'") and item.endswith("'"):
            #print("we remove the stuff for item", item)
            item = item[1:-1]
         
        if self.is_uri(item):
            item = "<"+item+">"
            return item
        elif self.is_var(item):
            return item
        elif item.startswith("<") and item.endswith(">"):
            return item
        else: 
            item = "'"+item+"'"
            #print("we add thing on", item)
            return item

#this used to be in the kb file, but since we dont use kbpedia as endpoint put it here.,
    def one_hop_graph(self, entity1_uri, relation_uri, entity2_uri):
        #print("THIS IS ENTITIES" ,entity1_uri,relation_uri, entity2_uri )
        if entity2_uri is None:
            entity2_uri = "?u_1"
        else:
            entity2_uri = entity2_uri
        
        entity1_uri = self.jena_formatting(entity1_uri)
        relation_uri = self.jena_formatting(relation_uri)
        entity2_uri = self.jena_formatting(entity2_uri)


        query_types = [u"{ent1} {rel} {ent2}",

                       ]
        where = ""
        for i in range(len(query_types)):
            #print("THIS IS I", i)
                        
            where = where + u"UNION {{ values ?m {{ {} }} {{select ?u_1 where {{ {} }} }} }}\n". \
                format(i,
                       query_types[
                           i].format(
                           rel=relation_uri,
                           ent1=entity1_uri,
                           ent2=entity2_uri,
                           type = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>",
                           prefix = ""
                           ))
        where = where[6:]
        
        #print("THIS IS WHERE WE HAVE THE UNION THING DO WE SEND IN MORE THAN ONE THING?",where)
        #where = self.transform_q_into_jena(where)

        query = u"""{prefix}
SELECT DISTINCT ?m WHERE {{ {where} }} """.format(prefix="", where=where)
        
        response = requests.get("http://localhost:3030/dbpedia/sparql", params={"query": query})
        #print("onehope results",query)

        if response.status_code == 200:
            results = response.json()
            output = results["results"]["bindings"]
            
            return output
            # Process the results
        #else:
            #print("Query failed with status code", response.status_code)

    def __one_hop_graph(self, entity_items, relation_items, threshold=None, number_of_entities=1):
        #print("WE ARE IN ONE HOP WITH E R ",entity_items, relation_items)

        all_combinations = self.create_all_combinations(entity_items,relation_items,'1')
        #print("THIS IS ALL THE COBINATIONS", all_combinations)

        with tqdm(total=len(all_combinations)) as progress_bar:
            for tripple in all_combinations:
                progress_bar.update(1)
                #print("sending in ",tripple[0], tripple[1],tripple[2])
                result = self.one_hop_graph(tripple[0], tripple[1],tripple[2])
                #print(result)
                if result is not None:
                            #tripple[0] == subject  tripple[1] == predicate tripple[2] == object
                            for item in result:
                                m = int(item["m"]["value"])
                                uri = tripple[2] if tripple[2] is not None else 0
                                if m == 0:
                                    n_s = self.create_or_get_node(tripple[0], True)
                                    #print(entity_uri[0])
                                    n_d = self.create_or_get_node(uri, True)
                                    e = Edge(n_s, tripple[1], n_d)
                                    self.add_edge(e)
                                
        
    def find_minimal_subgraph(self, entity_items, relation_items, double_relation=False, ask_query=False,
                              sort_query=False, h1_threshold=None):
        self.entity_items, self.relation_items = MyList(entity_items), MyList(relation_items)

        if double_relation:
            self.relation_items.append(self.relation_items[0])

        # Find subgraphs that are consist of at least one entity and exactly one relation
        
        self.__one_hop_graph(self.entity_items, self.relation_items, number_of_entities=int(ask_query) + 1,
                             threshold=h1_threshold)
        for edge in self.edges:
            print("dest node",edge.dest_node)
            print("source_node",edge.source_node)
            print('edge',edge)
            print('\n')


        if len(self.edges) > 100:
            return

        
            



    def __get_generic_uri(self, uri, edges):
        return Uri.generic_uri(uri)

    def generalize_nodes(self):
        """
        if there are nodes which have none-generic uri that is not in the list of possible entity/relation,
        such uris will be replaced by a generic uri
        :return: None
        """
        uris = sum([items.uris for items in self.entity_items] + [items.uris for items in self.relation_items], [])
        for node in self.nodes:
            for uri in node.uris:
                if uri not in uris and not uri.is_generic():
                    generic_uri = self.__get_generic_uri(uri, node.inbound + node.outbound)
                    node.replace_uri(uri, generic_uri)

    def merge_edges(self):
        to_be_removed = set()
        for edge_1 in self.edges:
            for edge_2 in self.edges:
                if edge_1 is edge_2 or edge_2 in to_be_removed:
                    continue
                if edge_1 == edge_2:
                    to_be_removed.add(edge_2)
        for item in to_be_removed:
            try:
                self.remove_edge(item)
            except:
                print('not remove edge')

    def __str__(self):
        return "\n".join([edge.full_path() for edge in self.edges])

