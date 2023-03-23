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



def query(args):
    q, idx = args
    payload = {'query': q, 'format': 'application/json'}
    try:
        jena_response = requests.get('http://localhost:3030/dbpedia/query', params={"query": q})
        #print(q,jena_response.json())
    except:
        return 0, None, idx
    return jena_response.status_code, jena_response.json() if jena_response.status_code == 200 else None, idx



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
           
    def create_all_combinations(self,entites, relations):
        all_entites =[]
        all_relations=[]
        #print(all_entites)
        if len(entites)<1:
            all_entites.append('?u2')
        else:
            for entity in entites:
                all_entites.append(entity['uri'])

        if len(relations)<1:
            all_relations.append('?u2')
        else:
            for relation in relations:
                all_relations.append(relation['uri'])
        
        #print(all_entites)
        #print(all_relations)
#this is taken from the first lines of the algorithm in the paper

        set1_e_p_e = set(itertools.product(all_entites,all_relations,all_entites))
        set2_e_p_uri = set(itertools.product(all_entites,all_relations,['?u1']))
        set3_uri_p_e = set(itertools.product(['?u1'],all_relations,all_entites))
        all_sets = set1_e_p_e|set2_e_p_uri|set3_uri_p_e
        #print(all_sets)
        #remove all the variables that are used twice aka izzyrybz <http://dbpedia.org/ontology/description> izzyrybz
        unique_set = set()
        for tup in all_sets:
            if all(tup.count(item) == 1 for item in tup):
                unique_set.add(tup)
        all_sets = unique_set

        

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
            entity2_uri = "?u1"
        else:
            entity2_uri = entity2_uri
        
        entity1_uri = self.jena_formatting(entity1_uri)
        relation_uri = self.jena_formatting(relation_uri)
        entity2_uri = self.jena_formatting(entity2_uri)


        query_types = [u"{ent2} {rel} {ent1}",
                       u"{ent1} {rel} {ent2}",
                       u"?u1 {type} {rel}",
                       u"?u2 {rel} ?u1",
                       ]
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
                           type = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>",
                           prefix = ""
                           ))
        where = where[6:]
        
        #print("THIS IS WHERE WE HAVE THE UNION THING DO WE SEND IN MORE THAN ONE THING?",where)
        #where = self.transform_q_into_jena(where)

        query = u"""{prefix}
SELECT DISTINCT ?m WHERE {{ {where} }} """.format(prefix="", where=where)
        
        response = requests.get("http://localhost:3030/dbpedia/sparql", params={"query": query})

        if response.status_code == 200:
            results = response.json()
            output = results["results"]["bindings"]
            return output
            # Process the results
        #else:
            #print("Query failed with status code", response.status_code)

    def __one_hop_graph(self, entity_items, relation_items, threshold=None, number_of_entities=1):
        #print("WE ARE IN ONE HOP WITH E R ",entity_items, relation_items)

        all_combinations = self.create_all_combinations(entity_items,relation_items)
        #print("THIS IS ALL THE COBINATIONS", all_combinations)

        with tqdm(total=len(all_combinations)) as progress_bar:
            for tripple in all_combinations:
                progress_bar.update(1)
                #print("sending in ",tripple[0], tripple[1],tripple[2])
                result = self.one_hop_graph(tripple[0], tripple[1],tripple[2])
                if result is not None:
                            #print("THIS IS RESLUT", result)
                            for item in result:
                                m = int(item["m"]["value"])
                                uri = tripple[2] if tripple[2] is not None else 0
                                if m == 0:
                                    n_s = self.create_or_get_node(uri, True)
                                    #print(entity_uri[0])
                                    n_d = self.create_or_get_node(tripple[0])
                                    e = Edge(n_s, tripple[1], n_d)
                                    self.add_edge(e)
                                elif m == 1:
                                    n_s = self.create_or_get_node(tripple[0])
                                    n_d = self.create_or_get_node(uri, True)
                                    e = Edge(n_s, tripple[1], n_d)
                                    self.add_edge(e)
                                elif m == 2:
                                    n_s = self.create_or_get_node(uri)
                                    n_d = self.create_or_get_node(tripple[1])
                                    e = Edge(n_s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', n_d)
                                    #not sure what to do about that
                                    self.add_edge(e)
                                elif m == 3:
                                    #print(tripple[1],uri,tripple[2],tripple[0])
                                    
                                    n_s = self.create_or_get_node('?u1')
                                    n_d = self.create_or_get_node('?u2')
                                    e = Edge(n_s, tripple[1], n_d)
                                    
                                    #not sure what to do about that
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

        #self.__extend_edges(self.edges, relation_items)

        # print('extend_edges: ')
        # for edge in self.edges:
        #     print(edge.source_node, edge, edge.dest_node)


    def __extend_edges(self, edges, relation_items):
        new_edges = set()
        total = 0
        for relation_item in relation_items:
            
            for relation_uri in relation_item['uri']:
                total += len(edges)
        with tqdm(total=total) as pbar:
            for relation_item in relation_items:
                for relation_uri in relation_item['uri']:
                    for edge in edges:
                        pbar.update(1)
                        new_edges.update(self.__extend_edge(edge, relation_uri))
        for e in new_edges:
            self.add_edge(e)

    def __extend_edge(self, edge, relation_uri):
        output = set()
        var_node = edge.source_node.uris
        '''if edge.source_node.are_all_uris_generic():
            var_node = edge.source_node
        if edge.dest_node.are_all_uris_generic():
            var_node = edge.dest_node'''
        ent1 = edge.source_node.uris
        ent2 = edge.dest_node.uris
        if not (var_node is None or ent1 is None or ent2 is None):
            result = self.two_hop_graph(ent1, edge.uri, ent2, relation_uri)
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
                            e = Edge(n_s, "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", n_d)
                            output.add(e)
        return output
    def two_hop_graph_template(self, entity1_uri, relation1_uri, entity2_uri, relation2_uri):
        # print('kb two_hop_graph_template')
        query_types = [[0, u"{ent1} {rel1} {ent2} . ?u1 {rel2} {ent1}"],
                       [1, u"{ent1} {rel1} {ent2} . {ent1} {rel2} ?u1"],
                       [2, u"{ent1} {rel1} {ent2} . {ent2} {rel2} ?u1"],
                       [3, u"{ent1} {rel1} {ent2} . ?u1 {rel2} {ent2}"],
                       [4, u"{ent1} {rel1} {ent2} . ?u1 {type} {rel2}"]]
        output = [[item[0], item[1].format(rel1=relation1_uri, ent1=entity1_uri,
                                           ent2=entity2_uri, rel2=relation2_uri,
                                           type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]
        # print('entity1_uri: ', entity1_uri)
        # print('entity2_uri: ', entity2_uri)
        # print('relation1_uri: ', relation1_uri)
        # print('relation2_uri: ', relation2_uri)
        # print('output: ', output)
        return output

    def two_hop_graph(self, entity1_uri, relation1_uri, entity2_uri, relation2_uri):
        # print('kb two_hop_graph')
        relation1_uri = self.jena_formatting(relation1_uri)
        relation2_uri = self.jena_formatting(relation2_uri)
        entity1_uri = self.jena_formatting(entity1_uri)
        entity2_uri = self.jena_formatting(entity2_uri)

        queries = self.two_hop_graph_template(entity1_uri, relation1_uri, entity2_uri, relation2_uri)
        output = None
        if len(queries) > 0:
            output = self.parallel_query(queries)
        # print('queries: ', queries)
        # print('output: ', output)
        return output
    
    def parallel_query(self, query_templates):
        args = []
        for i in range(len(query_templates)):
            args.append(
                ( u"{} ASK WHERE {{ {} }}".format("", query_templates[i][1]),
                 query_templates[i][0]))
        with closing(Pool(len(query_templates))) as pool:
            query_results = pool.map(query, args)
            pool.terminate()
            results = []
            for i in range(len(query_results)):
                if query_results[i][0] == 200:
                    results.append((query_results[i][2], query_results[i][1]["boolean"]))
            return results

    '''
            # Extend the existing edges with another hop
            self.__extend_edges(self.edges, relation_items)
            

        def __extend_edges(self, edges, relation_items):
            print('we are extending our edges')
            new_edges = set()
            total = 0
            
            #get all edges 
            edge_list=[]
            relation_list=[]
            for edge in edges:
                #print([edge.uri, edge.source_node.uris, edge.dest_node.uris])
                edge_list.append([edge.uri, edge.source_node.uris, edge.dest_node.uris])

            for relation_item in relation_items:
                #print(relation_item['uri'])
                relation_list.append(relation_item['uri'])
                
                for relation_uri in relation_item['uri']:
                    total += len(edges)

            #all_combinations_of_edges = self.create_all_combinations_for_edges(edge_list)
            for edge1,source1,dest1 in edge_list:
                for edge2,source2,dest2 in edge_list:
                    #print(edge1,source1,dest1)
                    #print(edge2,source2,dest2)
                    if edge1 is edge2 and source1 is source2 and dest1 is dest2:
                        continue
                    else:
                        
                        self.__extend_edge(edge1,source1,dest1, edge2,source2,dest2)

                #self.__extend_edge

            exit()
            #self.create_all_combinations()
            with tqdm(total=total) as progress_bar:
                for relation_item in relation_items:
                    print("this is extend edges relation item",relation_item, len(edges))
                    relation_uri = relation_item['uri']
                    for edge in edges:
                        progress_bar.update(1)
                        print("thisis the edge and relation uri",edge,relation_uri,edge.dest_node,edge.source_node)
                        new_edges.update(self.__extend_edge(edge, relation_uri))
            for e in new_edges:
                self.add_edge(e)

        def __extend_edge(self, edge1, source1 ,dest1 , edge2 ,source2, dest2):
            output = set()
            var_node = None

            result = self.two_hop_graph(edge1, source1 ,dest1 , edge2 ,source2, dest2)
            
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
                        
                print(result)
            
            print(output)
            #exit()
            return output

        def two_hop_graph_template(self, edge1, source1 ,dest1 , edge2 ,source2, dest2):
            # print('kb two_hop_graph_template')
            query_types = [[0, u"{source_node1} {rel1} {dest_node1} . {source_node2} {rel2} {dest_node2}"],
                        [1, u"{dest_node1} {rel1} {source_node1} . {dest_node2} {rel2} {source_node2}"],
                        [2, u"{source_node1} {rel1} {dest_node1} . {dest_node2} {rel2} {source_node2}"],
                        [3, u"{dest_node1} {rel1} {source_node1} . {source_node2} {rel2} {dest_node2}"],
                        [4, u"{source_node1} {rel1} {dest_node1} . {source_node2} {rel2} ?u3 "],
                        [5, u"{dest_node1} {rel1} {source_node1} . {dest_node2} {rel2} ?u3"],
                        [6, u"{source_node1} {rel1} ?u3 . {source_node2} {rel2} {dest_node2}"],
                        [7, u"{dest_node2} {rel1} ?u3' . {source_node2} {rel2} {dest_node2}"]
                        ]
            #could use extension
            output = [[item[0], item[1].format(rel1=edge1, source_node1=source1,
                                            dest_node1=dest1, rel2=edge2,
                                                source_node2=source2,dest_node2=dest2, 
                                            type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]
            # print('entity1_uri: ', entity1_uri)
            #SELECT ?u1 WHERE { ?u1 <http://example.org/action/delete> ?u2. ?u1 <http://example.org/action/modify> ?u3 }
            # print('entity2_uri: ', entity2_uri)
            # print('relation1_uri: ', relation1_uri)
            # print('relation2_uri: ', relation2_uri)
            print('output: ', output)
            
            return output

        def two_hop_graph(self, edge1, source1 ,dest1 , edge2 ,source2, dest2):
            # print('kb two_hop_graph')
            edge1 = self.jena_formatting(edge1)
            source1 = self.jena_formatting(source1)
            dest1 = self.jena_formatting(dest1)
            edge2 = self.jena_formatting(edge2)
            source2 = self.jena_formatting(source2)
            dest2 = self.jena_formatting(dest2)

            queries = self.two_hop_graph_template(edge1, source1 ,dest1 , edge2 ,source2, dest2)
            
            output = None
            if len(queries) > 0:
                #ye this might get fucked
                output = self.parallel_query(queries)
            # print('queries: ', queries)
            print('output: ', output)
            return output

        def parallel_query(self,query_templates):
            
            args = []
            for i in range(len(query_templates)):
                args.append(
                    (u"{} ASK WHERE {{ {} }}".format("", query_templates[i][1]),
                    query_templates[i][0]))
            with closing(Pool(len(query_templates))) as pool:
                query_results = pool.map(query, args)
                pool.terminate()
                results = []
                for i in range(len(query_results)):
                    if query_results[i][0] == 200:
                        results.append((query_results[i][2], query_results[i][1]["boolean"]))
                print("THIS IS THE RESULTS FOR THE QUERY",results)
                return results
    '''

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

