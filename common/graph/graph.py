import requests
from common.graph.node import Node
from common.graph.edge import Edge
from common.container.uri import Uri
from common.container.linkeditem import LinkedItem
from common.utility.mylist import MyList
import itertools
import logging
from tqdm import tqdm
from urllib.parse import urlparse

def is_uri(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
def is_var(string):
    if string[0] == '?':
        return True
    else:
        return False



class Graph:
    def __init__(self, kb, ):
        self.kb = kb
        self.nodes, self.edges = set(), set()
        self.entity_items, self.relation_items = [], []
        self.suggest_retrieve_id = 0

    def create_or_get_node(self, uris, mergable=False):
        if isinstance(uris, (int)):
            uris = self.__get_generic_uri(uris, 0)
            mergable = True
        print("create_or_get_node",uris)
        new_node = Node(uris, mergable)
        print("past node ", new_node)
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
        for relation_item in relation_items:
            rel_uris_len = len(relation_item['uri'])
            for entity_uris in itertools.product(*[items for items in entity_items]):
                total += rel_uris_len * len(list(itertools.combinations(entity_uris, number_of_entities)))
        return total

    def transform_q_into_jena(self, query):
        query = query.split()
        
        for i,item in enumerate(query):
            if item in 'where' and query[i+1] in '{':
                for tripple_index in range(2,5):
                    current_tripple = query[i+tripple_index]
                    if(is_uri(current_tripple)):
                        current_tripple = "<"+current_tripple+">"
                        query[i+tripple_index] = current_tripple
                        #print(current_tripple)
                    elif(not is_var(current_tripple)):
                        current_tripple = "'"+current_tripple+"'"
                        query[i+tripple_index] = current_tripple
                        #print(current_tripple)
        delimiter = " "
        query = delimiter.join(query)
        return query
            

#this used to be in the kb file, but since we dont use kbpedia as endpoint put it here.,
    def one_hop_graph(self, entity1_uri, relation_uri, entity2_uri=None):
        # print('kb one_hop_graph')
        #print("THIS IS RELATION URI" ,relation_uri,entity1_uri)
        #relation_uri = self.uri_to_sparql(relation_uri)
        #entity1_uri = self.uri_to_sparql(entity1_uri)
        if entity2_uri is None:
            entity2_uri = "?u1"
        else:
            entity2_uri = entity2_uri

        query_types = [u"{ent2} {rel} {ent1}",
                       u"{ent1} {rel} {ent2}",
                       u"?u1 {type} {rel}"]
        where = ""
        for i in range(len(query_types)):
            #print("THIS IS I", i)
            
                        
            where = where + u"UNION {{ values ?m {{ {} }} {{select ?u1 where {{ {} }} }} }}\n". \
                format(i,
                       query_types[
                           i].format(
                           rel=relation_uri,
                           ent1=entity1_uri,
                           ent2=entity2_uri,
                           #WTF e type_uri, dbpedia ???
                           #type=self.type_uri,
                           type = "?o",

                           #query_prefix() returnerar en tom sträng???
                           #prefix=self.query_prefix()))
                           prefix = ""
                           ))
        where = where[6:]
        where = self.transform_q_into_jena(where)

        #print("THIS IS WHERE" , )
        query = u"""{prefix}
SELECT DISTINCT ?m WHERE {{ {where} }} """.format(prefix="", where=where)
        
       

        
        #print("THIS IS Q"  ,query)
        #OKEJ SO THEY START QUERYING HERE ;WHY???
        
        response = requests.get("http://localhost:3030/dbpedia/sparql", params={"query": query})

        if response.status_code == 200:
            results = response.json()
            output = results["results"]["bindings"]
            return output
            # Process the results
        else:
            print("Query failed with status code", response.status_code)


        '''status, response = self.query(query)
        if status == 200 and len(response["results"]["bindings"]) > 0:
            output = response["results"]["bindings"]
            return output
        '''        

    def __one_hop_graph(self, entity_items, relation_items, threshold=None, number_of_entities=1):
        #print("WE ARE IN ONE HOP WITH E R ",entity_items, relation_items)

        total = self.count_combinations(entity_items, relation_items, number_of_entities)
        #print("THIS IS TOTAL " ,total)
        if threshold is not None:
            #print(threshold)
            while total > threshold:
                print("we are stuck")
                total = self.count_combinations(entity_items, relation_items, number_of_entities)

        with tqdm(total=total) as progress_bar:
            print("we are tqdm")
            all_entity_uris = []
            for relation_item in relation_items:
                relation_uri = relation_item['uri']
                for item in entity_items:
                        all_entity_uris.append(item['uri'])
                combinations_entity = itertools.combinations(all_entity_uris,2)
                
                for entity_uris in combinations_entity:
                    #print("gick den sönder ",entity_uris)
                    for entity_uri in itertools.combinations(entity_uris, number_of_entities):
                        progress_bar.update(1)
                        #print("HERE")

                        #this one is different?

                        result = self.one_hop_graph(entity_uri[0], relation_uri,
                                                        entity_uri[1] if len(entity_uri) > 1 else None)
                        #The result is a query answer, so idk why

                        if result is not None:
                            for item in result:
                                m = int(item["m"]["value"])
                                uri = entity_uri[1] if len(entity_uri) > 1 else 0
                                if m == 0:
                                    n_s = self.create_or_get_node(uri, True)
                                    #print(entity_uri[0])
                                    n_d = self.create_or_get_node(entity_uri[0])
                                    e = Edge(n_s, relation_uri, n_d)
                                    self.add_edge(e)
                                elif m == 1:
                                    n_s = self.create_or_get_node(entity_uri[0])
                                    n_d = self.create_or_get_node(uri, True)
                                    e = Edge(n_s, relation_uri, n_d)
                                    self.add_edge(e)
                                elif m == 2:
                                    n_s = self.create_or_get_node(uri)
                                    n_d = self.create_or_get_node(relation_uri)
                                    e = Edge(n_s, Uri(self.kb.type_uri, self.kb.parse_uri), n_d)
                                    self.add_edge(e)
            for edge in self.edges:
                print(edge)

    def find_minimal_subgraph(self, entity_items, relation_items, double_relation=False, ask_query=False,
                              sort_query=False, h1_threshold=None):
        self.entity_items, self.relation_items = MyList(entity_items), MyList(relation_items)

        if double_relation:
            self.relation_items.append(self.relation_items[0])

        # Find subgraphs that are consist of at least one entity and exactly one relation
        # self.logger.info("start finding one hop graph")
        self.__one_hop_graph(self.entity_items, self.relation_items, number_of_entities=int(ask_query) + 1,
                             threshold=h1_threshold)
        # self.logger.info("finding one hop graph finished")
        # print('one hop graph: ')
        # for edge in self.edges:
        #     print(edge.source_node, edge, edge.dest_node)

        if len(self.edges) > 100:
            return

        # Extend the existing edges with another hop
        # self.logger.info("Extend edges with another hop")
        self.__extend_edges(self.edges, relation_items)

        # print('extend_edges: ')
        # for edge in self.edges:
        #     print(edge.source_node, edge, edge.dest_node)


    def __extend_edges(self, edges, relation_items):
        new_edges = set()
        total = 0
        for relation_item in relation_items:
            for relation_uri in relation_item.uris:
                total += len(edges)
        with tqdm(total=total) as progress_bar:
            for relation_item in relation_items:
                for relation_uri in relation_item.uris:
                    for edge in edges:
                        progress_bar.update(1)
                        new_edges.update(self.__extend_edge(edge, relation_uri))
        for e in new_edges:
            self.add_edge(e)

    def __extend_edge(self, edge, relation_uri):
        output = set()
        var_node = None
        if edge.source_node.are_all_uris_generic():
            var_node = edge.source_node
        if edge.dest_node.are_all_uris_generic():
            var_node = edge.dest_node
        ent1 = edge.source_node.first_uri_if_only()
        ent2 = edge.dest_node.first_uri_if_only()
        if not (var_node is None or ent1 is None or ent2 is None):
            result = self.kb.two_hop_graph(ent1, edge.uri, ent2, relation_uri)
            if result is not None:
                for item in result:
                    if item[1]:
                        if item[0] == 0:
                            n_s = self.create_or_get_node(1, True)
                            n_d = var_node
                            e = Edge(n_s, relation_uri, n_d)
                            output.add(e)
                        elif item[0] == 1:
                            n_s = var_node
                            n_d = self.create_or_get_node(1, True)
                            e = Edge(n_s, relation_uri, n_d)
                            output.add(e)
                        elif item[0] == 2:
                            n_s = var_node
                            n_d = self.create_or_get_node(1, True)
                            e = Edge(n_s, relation_uri, n_d)
                            output.add(e)
                            self.suggest_retrieve_id = 1
                        elif item[0] == 3:
                            n_s = self.create_or_get_node(1, True)
                            n_d = var_node
                            e = Edge(n_s, relation_uri, n_d)
                            output.add(e)
                        elif item[0] == 4:
                            n_d = self.create_or_get_node(relation_uri)
                            n_s = self.create_or_get_node(1, True)
                            e = Edge(n_s, Uri(self.kb.type_uri, self.kb.parse_uri), n_d)
                            output.add(e)
        print(output)
        return output

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

