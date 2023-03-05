import requests
from common.graph.graph import Graph
from common.graph.path import Path

import numpy as np
import itertools


class Paths(list):
    def __init__(self, *args):
        super(Paths, self).__init__(*args)

    @property
    def confidence(self):
        """
        Cumulative product of paths' confidence
        :return:
        """
        return np.prod([path.confidence for path in self])
    
    import itertools

    def to_where(self ,fuseki_endpoint, graph, ask_query=False):
        """
        Transform paths into where clauses
        :param fuseki_endpoint: The URL of the Fuseki endpoint to query
        :param ask_query: Whether to use an ASK query instead of a SELECT query
        :return: A list of suggested WHERE clauses for the path
        """
        output = []
        sparql_len = []
        graph = Graph()

        for batch_edges in self:
            print(batch_edges)
            #sparql_where = [self.sparql_format_jena(edge) for edge in batch_edges]
            for edge in batch_edges:
                edge_elements = [edge.source_node, edge, edge.dest_node]
                sparql_where = self.sparql_format_jena(graph,edge_elements)
                print("Where",sparql_where)
                output.append(sparql_where)
        

                #edge = edge_elements[1] is saved as uri, and not uris which means you cannot loop through them
                if(graph.is_var(edge_elements[0].uris.strip("'"))):
                    sparql_q_varible_num = edge_elements[0].uris.strip("'")
                
                elif(graph.is_var(edge_elements[1].uri.strip("'"))):
                    sparql_q_varible_num = edge_elements[1].uri.strip("'")[-1]
            
                elif(graph.is_var(edge_elements[2].uris.strip("'"))):
                    sparql_q_varible_num = edge_elements[2].uris.strip("'")[-1]

                else:
                    sparql_q_varible_num = '?u1'

                print(sparql_q_varible_num)

                #Prev if ask_query:
                output.append({"suggested_id": sparql_q_varible_num, "where": sparql_where})
                
                # Prev else:
                '''for L in range(1, len(sparql_where) + 1):
                    print("this is L",L)
                    #for subset in itertools.combinations(sparql_where, L):
                #I dont understand why we need to do this...
                    result = self.query_fuseki_endpoint(fuseki_endpoint, subset, count=True)
                    if result is not None:
                        result = int(result["results"]["bindings"][0]["callret-0"]["value"])
                        if result > 0:
                            #Prev output.append({"suggested_id": max_generic_id, "where": subset})
                            output.append({"where": subset})
                            sparql_len.append(len(subset))'''
        #print("THHIS IS OUTPUT",output)
        return output
    
    def sparql_format_jena(self,graph,edge_elements):
        #graph = Graph()
        
        #print("before",source_node,edge,destination_node)
        source_node = graph.jena_formatting(edge_elements[0].uris.strip("'"))
        edge = graph.jena_formatting(edge_elements[1].uri.strip("'"))
        destination_node = graph.jena_formatting(edge_elements[2].uris.strip("'"))
        #print("after",source_node,edge,destination_node)
        where_clause = str(source_node) + " " + str(edge) + " " + str(destination_node) 

        return where_clause
        




    

    def add(self, new_paths):#, validity_fn):
        """
        Append new paths if they pass the validity check
        :param new_paths:
        :param validity_fn:
        :return:
        """
        
        for path in new_paths:
            if (len(self) == 0 or path not in self) :#and validity_fn(path):
                self.append(path)

    def extend(self, new_edge):
        """
        Create a new <Paths> that contains path of current <Paths> which the new_edge if possible is appended to each
        :param new_edge:
        :return:
        """
        new_output = []
        if len(self) == 0:
            self.append(Path([]))
        for item in self:
            if item.addable(new_edge):
                path = Path()
                for edge in item:
                    if edge.uri == new_edge.uri and \
                            edge.source_node.are_all_uris_generic() and \
                            edge.dest_node.are_all_uris_generic() and \
                            not (
                                    new_edge.source_node.are_all_uris_generic() and new_edge.dest_node.are_all_uris_generic()):
                        pass
                    else:
                        path.append(edge)
                new_output.append(Path(path + [new_edge]))
            else:
                new_output.append(item)
        return Paths(new_output)

    def remove_duplicates(self):
        removed_duplicate_paths = []
        paths_str = [str(path) for path in self]
        for idx in range(len(self)):
            if paths_str[idx] not in paths_str[idx + 1:]:
                removed_duplicate_paths.append(self[idx])

        return Paths(removed_duplicate_paths)
