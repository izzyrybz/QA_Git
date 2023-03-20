import inspect
import json

import requests
from common.container.answerset import AnswerSet
from common.container.linkeditem import LinkedItem
from common.graph.path import Path
from common.graph.paths import Paths
from common.utility.mylist import MyList
from rdflib import Graph, Namespace

from parser.lc_quad import LC_QaudParser


class QueryBuilder:

    def check_if_ontology_property_resource(self,uri):
        """
        Given a DBpedia URI, returns its type as "ontology", "property", or "entity".
        """
        g = Graph()
        dbpedia = Namespace("http://dbpedia.org/resource/")
        g.parse(str(uri))
        if uri.startswith(dbpedia):
            # Remove the "http://dbpedia.org/resource/" prefix
            local_name = uri.replace(str(dbpedia), '')
            if g.qname(local_name)[0] == "dbo":
                return "?o"
            elif g.qname(local_name)[0] == "dbp":
                return "?p"
            else:
                return "?s"
        else:
            raise ValueError("URI is not a DBpedia resource.")

    def is_w3_type(self,uri):
        return uri == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"



    def to_where_statement(self, graph, ask_query, count_query, sort_query):
        #dont think generalize_nodes is needed
        #graph.generalize_nodes()
        graph.merge_edges()
        #print("Do we even go in here")

        paths = self.__find_paths_start_with_entities(graph, graph.entity_items, graph.relation_items, graph.edges)
        for path in paths:
            for edge in path:
                print("this is edge",edge)

        paths = paths.remove_duplicates()

        # Expand coverage by changing generic ids
        new_paths = []
        for path in paths:
            to_be_updated_edges = []
            generic_nodes = set()
            for edge in path:
                #if edge.source_node.are_all_uris_generic():
                if self.is_w3_type(edge.source_node):
                    generic_nodes.add(edge.source_node)
                #if edge.dest_node.are_all_uris_generic():
                if self.is_w3_type(edge.dest_node):
                    generic_nodes.add(edge.dest_node)

                #if edge.source_node.are_all_uris_generic() and not edge.dest_node.are_all_uris_generic():
                if self.is_w3_type(edge.source_node) and not self.is_w3_type(edge.dest_node):
                    to_be_updated_edges.append(
                        {"type": "source", "node": edge.source_node, "edge": edge})
                #if edge.dest_node.are_all_uris_generic() and not edge.source_node.are_all_uris_generic():
                if self.is_w3_type(edge.dest_node) and not self.is_w3_type(edge.source_node):
                    to_be_updated_edges.append(
                        {"type": "dest", "node": edge.dest_node, "edge": edge})

            for new_node in generic_nodes:
                for edge_info in to_be_updated_edges:
                    if edge_info["node"] != new_node:
                        new_path = None
                        if edge_info["type"] == "source":
                            new_path = path.replace_edge(edge_info["edge"],
                                                         edge_info["edge"].copy(source_node=new_node))
                        if edge_info["type"] == "dest":
                            new_path = path.replace_edge(edge_info["edge"], edge_info["edge"].copy(dest_node=new_node))
                        if new_path is not None:
                            new_paths.append(new_path)

        new_paths = Paths(new_paths).remove_duplicates()
    

        for new_path in new_paths:
            paths.append(new_path)
        paths = paths.remove_duplicates()

        for path in paths:
            for edge in path:
                print("DEST NODE" ,edge.dest_node)
                print("SOURCe NODE" ,edge.source_node)
                print("edge" ,edge)

        #Prev : paths.sort(key=lambda x: x.confidence, reverse=True)
        fuseki_endpoint="http://localhost:3030/dbpedia/sparql"
        
        output = paths.to_where(fuseki_endpoint,graph, ask_query)
        

        # Remove queries with no answer
        filtered_output = []
        
        for where_clause in output:
            #print("HELLOOOO",where_clause)

            #Prev : target_var = where_clause["suggested_id"]
            response = self.query_fuseki_endpoint(fuseki_endpoint,where_clause,
                                              count=count_query,
                                
                                              ask=ask_query)
            #print(response)
                       
            if response is not None:
                raw_answer =response[0]
                sparlq_q =response[1]
                #print(raw_answer)
                bindings = raw_answer['results']['bindings']
                #Prev : answerset = AnswerSet(raw_answer, parser.parse_queryresult)
                answer={}
                target_vars = 'u1','u2'
                
                # Do not include the query if it does not return any answer, except for boolean query
                if len(bindings) > 0 or ask_query:
                    # Extract values from bindings
                    for target_var in target_vars:
                        try:
                            values = [binding[target_var]['value'] for binding in bindings]
                            answer["target_var"] = bindings[0]
                            answer["answer"] = values
                            filtered_output.append(where_clause)
                            filtered_output.append(sparlq_q)
                        except:
                            continue
                

        #print(filtered_output)

        return filtered_output
    
    def query_fuseki_endpoint(self, fuseki_endpoint, where_clauses,count,ask):
        """
        Query a Jena Fuseki endpoint with the given WHERE clauses
        :param endpoint_url: The URL of the Fuseki endpoint to query
        :param where_clauses: A list of WHERE clauses to include in the query
        :param count: Whether to return the count of results instead of the results themselves
        :param ask: Whether to return the ask of results instead of the results themselves
        :return: The results of the query, or None if the query failed
        """
        if(ask):
            query_template= "ASK * WHERE {{ {} }}"

        elif(count):
            query_template = "SELECT (COUNT(*) AS ?count) WHERE {{ {} }}"
        else:
            query_template = "SELECT * WHERE {{ {} }}"
             
        #TODO ADD FUNC for dates
        query = query_template.format("".join(where_clauses))
        
        
        headers = {"Accept": "application/sparql-results+json"}
        response = requests.post(fuseki_endpoint, data={"query": query})
        
        
        if response.status_code == 200:
            return response.json(), query
        else:
            return None

    def __find_paths(self, graph, entity_items, relation_items, edges, output_paths=Paths(), used_edges=set()):
        new_output_paths = Paths([])
        

        if len(relation_items) == 0:
            if len(entity_items) > 0:
                
                return Paths()
            
            return output_paths

        used_relations = []
        for relation_item in relation_items:
            #print(relation_item)
            for relation in relation_item.uris:
                #print(relation)
                used_relations = used_relations + [relation]
                for edge in self.find_edges(edges, relation, used_edges):
                    entities = MyList()
                    if not (edge.source_node.are_all_uris_generic() or self.is_w3_type(edge.uri)):
                        entities.extend(edge.source_node.uris)
                    if not (edge.dest_node.are_all_uris_generic() or self.is_w3_type(edge.uri)):
                        entities.extend(edge.dest_node.uris)

                    entity_use = entity_items - LinkedItem.list_contains_uris(entity_items, entities)
                    relation_use = relation_items - LinkedItem.list_contains_uris(relation_items, used_relations)
                    edge_use = edges - {edge}

                    new_paths = self.__find_paths(graph,
                                                  entity_use,
                                                  relation_use,
                                                  edge_use,
                                                  output_paths=output_paths.extend(edge),
                                                  used_edges=used_edges | set([edge]))
                    new_output_paths.add(new_paths, lambda path: len(path) >= len(graph.relation_items))

        return new_output_paths

    def __find_paths_start_with_entities(self, graph, entity_items, relation_items, edges, output_paths=Paths(), used_edges=set()):
        new_output_paths = Paths([])
        #print("wtfw",relation_items)
        if len(entity_items) > 0:
            for entity_item in entity_items:
                
                entity = entity_item['uri']
                
                #Prev for entity in entity_item.uris:
                for edge in self.find_edges_by_entity(edges, entity, used_edges):
                    
                    if not self.is_w3_type(edge.uri):
                        used_relations = [edge.uri]

                    else:
                        
                        used_relations = edge.dest_node.uris
                    entities = MyList()
                    
                    # I think edge.source_node.are_all_uris_generic() looks to see if source node is <type> changed it

                    #if not (edge.source_node.are_all_uris_generic() or edge.uri.is_type()):
                    if not (self.is_w3_type(edge.source_node.uris) or self.is_w3_type(edge.uri)):
                        
                        entities.extend(edge.source_node.uris)
                    #if not (edge.dest_node.are_all_uris_generic() or edge.uri.is_type()):
                    if not (self.is_w3_type(edge.dest_node.uris) or self.is_w3_type(edge.uri)):    
                        
                        entities.extend(edge.dest_node.uris)
                    
                    #we remove the entities and relations we just checked 
                    
                    entity_use = entity_items - LinkedItem.list_contains_uris(entity_items, entities)
                    
                    relation_use = relation_items - LinkedItem.list_contains_uris(relation_items, used_relations)
                    
                    edge_use = edges - {edge}

                    #unsure if edge_use is trying to be smaller here?

                    new_paths = self.__find_paths(graph,
                                                    entity_use,
                                                    relation_use,
                                                    edge_use,
                                                    output_paths=output_paths.extend(edge),
                                                    used_edges=used_edges | set([edge]))
                    
                    #why does the path need to be bigger than the relationship_items
                    new_output_paths.add(new_paths)#, lambda path: len(path) >= len(graph.relation_items))
                    #print(new_output_paths)
            return new_output_paths
        else:
            if len(relation_items) > 0:
                for entity_item in relation_items:
                
                    entity = entity_item['uri']
                    
                    #Prev for entity in entity_item.uris:
                    for edge in self.find_edges_by_entity(edges, entity, used_edges):
                        
                        if not self.is_w3_type(edge.uri):
                            used_relations = [edge.uri]
                        
                        else:
                            
                            used_relations = edge.dest_node.uris
                        entities = MyList()
                        

                        # I think edge.source_node.are_all_uris_generic() looks to see if source node is <type> changed it

                        #if not (edge.source_node.are_all_uris_generic() or edge.uri.is_type()):
                        if not (self.is_w3_type(edge.source_node.uris) or self.is_w3_type(edge.uri)):
                            
                            entities.extend(edge.source_node.uris)


                        #if not (edge.dest_node.are_all_uris_generic() or edge.uri.is_type()):
                        if not (self.is_w3_type(edge.dest_node.uris) or self.is_w3_type(edge.uri)):    
                            
                            entities.extend(edge.dest_node.uris)
                        
                        
                        #we remove the entities and relations we just checked 
                        
                        entity_use = entity_items - LinkedItem.list_contains_uris(entity_items, entities)
                        
                        relation_use = relation_items - LinkedItem.list_contains_uris(relation_items, used_relations)
                        
                        edge_use = edges - {edge}

                        #unsure if edge_use is trying to be smaller here?

                        new_paths = self.__find_paths(graph,
                                                        entity_use,
                                                        relation_use,
                                                        edge_use,
                                                        output_paths=output_paths.extend(edge),
                                                        used_edges=used_edges | set([edge]))
                        
                        #why does the path need to be bigger than the relationship_items
                        new_output_paths.add(new_paths)#, lambda path: len(path) >= len(graph.relation_items))
                    #print(new_output_paths)    
            return new_output_paths
        

    def find_edges(self, edges, uri, used_edges):
        outputs = [edge for edge in edges if edge.uri == uri or (self.is_w3_type(edge.uri)) and edge.dest_node.has_uri(uri)]
        if len(used_edges) == 0:
            return outputs
        connected_edges = []
        for edge in outputs:
            found = False
            for used_edge in used_edges:
                if edge.source_node == used_edge.source_node or edge.source_node == used_edge.dest_node or \
                        edge.dest_node == used_edge.source_node or edge.dest_node == used_edge.dest_node:
                    found = True
                    break
            if found:
                connected_edges.append(edge)

        return connected_edges

    def find_edges_by_entity(self, edges, entity_uri, used_edges):
        outputs = [edge for edge in edges if
                   (edge.source_node.has_uri(entity_uri) or edge.dest_node.has_uri(entity_uri))]
    
        if len(used_edges) == 0:
            return outputs
        
            
        connected_edges = []
        for edge in outputs:
            
            found = False
            for used_edge in used_edges:
                
                if edge.source_node == used_edge.source_node or edge.source_node == used_edge.dest_node or \
                        edge.dest_node == used_edge.source_node or edge.dest_node == used_edge.dest_node:
                    found = True
                    break
            if found:
                connected_edges.append(edge)
        print("In find_edges_by_entity and these are the connected edges ",connected_edges)
        return connected_edges
