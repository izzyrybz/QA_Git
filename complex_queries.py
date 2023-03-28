from contextlib import closing
from multiprocessing import Pool
import requests
from tqdm import tqdm

from common.graph.graph import Graph



def query(args):
    q, idx = args
    payload = {'query': q, 'format': 'application/json'}
    try:
        jena_response = requests.get('http://localhost:3030/dbpedia/query', params={"query": q})
        #print(q,jena_response.json())
        return jena_response.status_code, jena_response.json(),q if jena_response.status_code == 200 else None, idx
        
    except:
        return 0, None, idx
    
  
def mutli_var_complex_query(valid_walks,ask_query,count_query):
    tripples = valid_walks[0::2]
    total = 0
    
    #get all edges 
    subject_predicate_object_list=[]
    #in what commits did izzrybz make
    #subject = ?u1 predicate = <author> object = izzyrybz
    
    for tripple in tripples:
        tripple = tripple.split()
        #print(tripple)
        subject_predicate_object_list.append([tripple[0], tripple[1], tripple[2]])
    
    #print(edge_list)

    #all_combinations_of_edges = self.create_all_combinations_for_edges(edge_list)
    count=0
    used_triples=[]
    total = len(tripples)*len(tripples)
    
    list_with_elements_and_sparql_final=[]
    with tqdm(total=total)as pbar:
    
        for subject1,predicate1,object1 in subject_predicate_object_list:
            for subject2,predicate2,object2 in subject_predicate_object_list:
                #print(edge2,source2,dest2,subject1,predicate1,dest1)
                if (subject1 == subject2 and predicate1 == predicate2 and object1 == object2) or ((subject1, predicate1, object1, subject2, predicate2, object2) in used_triples) or ((subject2, predicate2, object2, subject1, predicate1, object1) in used_triples):
                    # If the two triples are the same or have been used before, skip to the next iteration
                    pbar.update(1)
                    continue
                else:
                    
                    # If the two triples are different and have not been used before, add them to the used triples list and process them
                    #print(subject1, predicate1, object1, subject2, predicate2, object2)
                    used_triples.append((subject1, predicate1, object1, subject2, predicate2, object2))
                    list_with_elements_and_sparql_final.append(complex_query_process(subject1,predicate1,object1, subject2,predicate2,object2, ask_query,count_query))
                    pbar.update(1)

                
            #self.__extend_edge
        #print(used_triples)
        #print(list_with_elements_and_sparql_final)
    
    return list_with_elements_and_sparql_final
     

def complex_query_process(subject1,predicate1,object1, subject2,predicate2,object2,ask_query,count_query):
    output = set()
    var_node = None
    
    results = two_hop_graph(subject1,predicate1,object1, subject2,predicate2,object2)
    #print(result)
    #with tqdm(total=len(results)) as pbar:
    list_with_elements_and_sparql=[]
    if results is not None:
        for result in results:
            #valid_walks which we are trying append to has the format of
            # elements within query, such as ?u1 <http://example.org/action/delete> ?u3 
            # the sparql query SELECT * WHERE { + elements + }

            if(ask_query):
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq=result[0]

            elif(count_query):
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0].replace('ASK WHERE {', 'SELECT (COUNT(*) AS ?count) WHERE { ')
            else:
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0].replace('ASK WHERE {', 'SELECT * WHERE { ')
            
            if modified_query[-1] is '}':
                modified_query = modified_query.replace('}','')
            #print(str(modified_query))
            list_with_elements_and_sparql.append(str(modified_query))
            list_with_elements_and_sparql.append(str(modified_query_with_sparlq))
            
  
    return list_with_elements_and_sparql

def two_hop_graph_template(subject1,predicate1,object1,subject2,predicate2,object2):
    
    query_types = [[0, u"{subject1} {predicate1} {object1} . {subject2} {predicate2} {object2}"],
                    ]
        #could use extension
    output = [[item[0], item[1].format(predicate1=predicate1, subject1=subject1,
                                        object1=object1, predicate2=predicate2,
                                            subject2=subject2,object2=object2, 
                                        type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]

    return output
    #check if one of the items are of the type ?u1 <something> ?u2 because then we need to have 
    '''if graph.is_var(object2) and graph.is_var(subject2):
        query_types = [[0, u"{subject1} {predicate1} {object1} . {subject2} {predicate2} {object2}"],

                    [1, u"{subject2} {predicate1} {object1} . {subject2} {predicate2} {object2} "],

                    [3, u"{subject1} {predicate1} {subject2}  . {subject2} {predicate2} {object2}"],

                    [4, u"{object2} {predicate1} {object1} . {subject2} {predicate2} {object2} "],

                    [5, u"{subject1} {predicate1} {object2}  . {subject2} {predicate2} {object2}"],

                    ]
        #could use extension
        output = [[item[0], item[1].format(predicate1=predicate1, subject1=subject1,
                                        object1=object1, predicate2=predicate2,
                                            subject2=subject2,object2=object2, 
                                        type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]

        return output
    elif(graph.is_var(subject1) and graph.is_var(object1)):
        query_types = [[0, u"{subject1} {predicate1} {object1} . {subject2} {predicate2} {object2}"],

                    [1, u"{subject1} {predicate1} {object1} . {subject1} {predicate2} {object2} "],

                    [2, u"{subject1} {predicate1} {object1} . {subject2} {predicate2} {subject1}"],

                    [3, u"{subject1} {predicate1} {object1} . {object1} {predicate2} {object2}"],

                    [4, u"{subject1} {predicate1} {object1} . {subject2} {predicate2} {object1}"],

                    ]
        #could use extension
        output = [[item[0], item[1].format(predicate1=predicate1, subject1=subject1,
                                        object1=object1, predicate2=predicate2,
                                            subject2=subject2,object2=object2, 
                                        type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]

        return output
    
    else:
        
        # print('kb two_hop_graph_template')
        query_types = [[0, u"{subject1} {predicate1} {object1} . {subject2} {predicate2} {object2}"],

                    [1, u"{subject1} {predicate1} {object1} . {subject2} {predicate2} ?u3 "],

                    [2, u"{subject1} {predicate1} ?u3 . {subject2} {predicate2} {object2}"],

                    ]
        #could use extension
        output = [[item[0], item[1].format(predicate1=predicate1, subject1=subject1,
                                        object1=object1, predicate2=predicate2,
                                            subject2=subject2,object2=object2, 
                                        type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]

        return output'''

def two_hop_graph(subject1,predicate1,object1, subject2,predicate2,object2):
    # print('kb two_hop_graph')
    graph = Graph()
    
    subject1 = graph.jena_formatting(subject1)
    predicate1 = graph.jena_formatting(predicate1)
    object1 = graph.jena_formatting(object1)
    subject2 = graph.jena_formatting(subject2)
    predicate2 = graph.jena_formatting(predicate2)
    object2 = graph.jena_formatting(object2)
    queries = two_hop_graph_template(subject1,predicate1,object1, subject2,predicate2,object2)
    
    output = None
    if len(queries) > 0:
        #ye this might get fucked
        output = parallel_query(queries)    
    # print('queries: ', queries)
    #print('output: ', output)
    return output

def parallel_query(query_templates):
    
    args = []
    for i in range(len(query_templates)):
        args.append(
            (u"{} ASK WHERE {{ {} }}".format("", query_templates[i][1]),
            query_templates[i][0]))
    with closing(Pool(len(query_templates))) as pool:
        query_results = pool.map(query, args)
        pool.terminate()
        results = []
        
        #query_results[number within the template][0] = statuscode
        #query_results[number within the template][1] = response
        #query_results[number within the template][2] = q
        for i in range(len(query_results)):
            if query_results[i][0] == 200:
                results.append((query_results[i][2], query_results[i][1]["boolean"]))
                
        
        return results
