from contextlib import closing
from multiprocessing import Pool
import requests
from tqdm import tqdm

from common.graph.graph import Graph

def normalize_var_combo(combo):
    var_dict = {}
    next_var = 0
    normalized_combo = []
    for element in combo:
        if element.startswith("?u_"):
            if element not in var_dict:
                var_dict[element] = f"?u_{next_var}"
                next_var += 1
            normalized_combo.append(var_dict[element])
        else:
            normalized_combo.append(element)
    return tuple(normalized_combo)

def check_triples(subjects, predicates, objects, used_triples,used_var_combo,normalized_combo):
    graph = Graph()
    
    #print(used_var_combo)
    for i in range(len(subjects)):

        if normalized_combo in used_var_combo:
            return False


        for j in range(i+1, len(subjects)):
            # print("in check tripples ",subjects[j],  predicates[j], objects[j],subjects[i],predicates[i], objects[i] )
            # print("used tripples",used_triples)

            if (subjects[i], predicates[i], objects[i], subjects[j],  predicates[j], objects[j]) in used_triples:
                # print("we have found a used tripple")

                return False
            if (subjects[j],  predicates[j], objects[j], subjects[i], predicates[i], objects[i]) in used_triples:
                # print("we have found a used tripple2")

                return False
            # print(subjects[i], predicates[i], objects[i],subjects[j], predicates[j], objects[j])
            if subjects[i] == subjects[j] and objects[i] == objects[j] and predicates[i] == predicates[j]:
                # print("1.returning false for",subjects[i], predicates[i], objects[i],subjects[j], predicates[j], objects[j])
                return False
            if predicates[i] == predicates[j] and objects[i] == objects[j] and graph.is_var(subjects[i]) and graph.is_var(subjects[j]):
                # print("2.returning false for",subjects[i], predicates[i], objects[i],subjects[j], predicates[j], objects[j])

                return False
            if predicates[i] == predicates[j] and graph.is_var(objects[i]) and graph.is_var(subjects[i]):

                return False
            if predicates[i] == predicates[j] and graph.is_var(objects[j]) and graph.is_var(subjects[j]):

                return False
            if graph.is_var(subjects[i]) and graph.is_var(subjects[j]) and predicates[i] == predicates[j] and graph.is_var(objects[i]) and graph.is_var(objects[j]):
                # print("2.returning false for",subjects[i], predicates[i], objects[i],subjects[j], predicates[j], objects[j])
                return False
            if not 'action' in predicates[i] and 'action' in predicates[j] or 'action' in predicates[i] and not 'action' in predicates[j]:
                if graph.is_var(objects[i]) and graph.is_var(objects[j]) and objects[i] == objects[j]:
                    #print("2.returning false for", subjects[i], predicates[i],objects[i], subjects[j], predicates[j], objects[j])
                    return False
        if predicates[i] in objects or subjects[i] in objects or predicates[i] in subjects:
            return False

    # print(subjects)
    if '?u_1' not in subjects and '?u_1' not in objects and '?u_1' not in predicates:
        return False

    return True


def query(args):
    q, idx = args
    payload = {'query': q, 'format': 'application/json'}
    try:
        jena_response = requests.get(
            'http://localhost:3030/dbpedia/query', params={"query": q})
        # print(q,jena_response.json())
        return jena_response.status_code, jena_response.json(), q if jena_response.status_code == 200 else None, idx

    except:
        return 0, None, idx


def mutli_var_complex_query(valid_walks, ask_query, count_query):
    tripples = valid_walks[0::2]
    graph = Graph()
    total = 0

    entities = []
    rel = []

    # get all edges
    subject_predicate_object_list = []
    # in what commits did izzrybz make
    # subject = ?u1 predicate = <author> object = izzyrybz

    for tripple in tripples:
        tripple = tripple.split()
        entities.append(tripple[2])
        entities.append(tripple[0])
        # combination_of_tripples = (graph.create_all_combinations(entities, tripple[1],'3'))
        # print("we are in complex queries",tripple)

        subject_predicate_object_list.append(
            [tripple[0], tripple[1], tripple[2]])
    # print("we are in complex queries",combination_of_tripples)

    # print(edge_list)

    # all_combinations_of_edges = self.create_all_combinations_for_edges(edge_list)
    count = 0
    used_triples_double = []
    used_var_combo=set()
    used_triples_tripple = []
    total = len(tripples)*len(tripples)

    list_with_elements_and_sparql_final = []
    with tqdm(total=total)as pbar:

        for subject1, predicate1, object1 in subject_predicate_object_list:
            for subject2, predicate2, object2 in subject_predicate_object_list:
                # print(edge2,source2,dest2,subject1,predicate1,dest1)
                # if (subject1 == subject2 and predicate1 == predicate2 and object1 == object2) or ((subject1, predicate1, object1, subject2, predicate2, object2) in used_triples_double) or ((subject2, predicate2, object2, subject1, predicate1, object1) in used_triples_double):
                normalized_combo = normalize_var_combo((subject1, predicate1, object1, subject2, predicate2, object2))
                if (not check_triples([subject1, subject2], [predicate1, predicate2], [object1, object2], used_triples_double,used_var_combo,normalized_combo)):
                    # If the two triples are the same or have been used before, skip to the next iteration
                    pbar.update(1)
                    continue
                else:

                    # If the two triples are different and have not been used before, add them to the used triples list and process them
                    # print(subject1, predicate1, object1, subject2, predicate2, object2)
                    used_triples_double.append(
                        (subject1, predicate1, object1, subject2, predicate2, object2))
                    #print((subject1, predicate1, object1, subject2, predicate2, object2))
                    used_var_combo.add(normalized_combo)
                    list_with_elements_and_sparql_final.append(two_hop_complex_query_process(
                        subject1, predicate1, object1, subject2, predicate2, object2, ask_query, count_query))
                    pbar.update(1)

        ########### tripple relation ########

    # tripple_statment=input("ideally we would put ranking here")
    tripple_statment = '1'
    used_var_combo=set()

    if (tripple_statment == '1'):
        with tqdm(total=total*len(tripples))as pbar:
            for subject1, predicate1, object1 in subject_predicate_object_list:
                for subject2, predicate2, object2 in subject_predicate_object_list:
                    for subject3, predicate3, object3 in subject_predicate_object_list:
                        normalized_combo = normalize_var_combo((subject1, predicate1, object1, subject2, predicate2, object2, subject3, predicate3, object3))
                        if (not check_triples([subject1, subject2, subject3], [predicate1, predicate2, predicate3], [object1, object2, object3], used_triples_tripple,used_var_combo,normalized_combo)):
                            # If the two triples are the same or have been used before, skip to the next iteration
                            pbar.update(1)
                            continue
                        else:
                            # If the two triples are different and have not been used before, add them to the used triples list and process them
                            # print(subject1, predicate1, object1, subject2, predicate2, object2)
                            used_triples_tripple.append(
                                (subject1, predicate1, object1, subject2, predicate2, object2, subject3, predicate3, object3))
                            

                            used_var_combo.add(normalized_combo)

                            list_with_elements_and_sparql_final.append(three_hop_complex_query_process(
                                subject1, predicate1, object1, subject2, predicate2, object2, subject3, predicate3, object3, ask_query, count_query))
                            pbar.update(1)
                            # print(list_with_elements_and_sparql_final)

    return list_with_elements_and_sparql_final


def three_hop_complex_query_process(subject1, predicate1, object1, subject2, predicate2, object2, subject3, predicate3, object3, ask_query, count_query):
    output = set()
    var_node = None

    results = three_hop_graph(subject1, predicate1, object1,
                              subject2, predicate2, object2, subject3, predicate3, object3)
    # print(result)
    # with tqdm(total=len(results)) as pbar:
    list_with_elements_and_sparql = []
    if results is not None:
        for result in results:
            # valid_walks which we are trying append to has the format of
            # elements within query, such as ?u1 <http://example.org/action/delete> ?u3
            # the sparql query SELECT * WHERE { + elements + }

            if (ask_query):
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0]

            elif (count_query):
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0].replace(
                    'ASK WHERE {', 'SELECT (COUNT(*) AS ?count) WHERE { ')
            else:
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0].replace(
                    'ASK WHERE {', 'SELECT * WHERE { ')

            if modified_query[-1] is '}':
                modified_query = modified_query.replace('}', '')
            # print(str(modified_query))
            list_with_elements_and_sparql.append(str(modified_query))
            list_with_elements_and_sparql.append(
                str(modified_query_with_sparlq))

    return list_with_elements_and_sparql


def two_hop_complex_query_process(subject1, predicate1, object1, subject2, predicate2, object2, ask_query, count_query):
    output = set()
    var_node = None

    results = two_hop_graph(subject1, predicate1, object1,
                            subject2, predicate2, object2)
    # print(result)
    # with tqdm(total=len(results)) as pbar:
    list_with_elements_and_sparql = []
    if results is not None:
        for result in results:
            # valid_walks which we are trying append to has the format of
            # elements within query, such as ?u1 <http://example.org/action/delete> ?u3
            # the sparql query SELECT * WHERE { + elements + }

            if (ask_query):
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0]

            elif (count_query):
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0].replace(
                    'ASK WHERE {', 'SELECT (COUNT(*) AS ?count) WHERE { ')
            else:
                modified_query = result[0].replace('ASK WHERE {', '')
                modified_query_with_sparlq = result[0].replace(
                    'ASK WHERE {', 'SELECT * WHERE { ')

            if modified_query[-1] is '}':
                modified_query = modified_query.replace('}', '')
            # print(str(modified_query))
            list_with_elements_and_sparql.append(str(modified_query))
            list_with_elements_and_sparql.append(
                str(modified_query_with_sparlq))

    return list_with_elements_and_sparql


def two_hop_graph_template(subject1, predicate1, object1, subject2, predicate2, object2):

    query_types = [[0, u"{subject1} {predicate1} {object1} .{subject2} {predicate2} {object2}"],
                   ]
    # could use extension
    output = [[item[0], item[1].format(predicate1=predicate1, subject1=subject1,
                                       object1=object1, predicate2=predicate2,
                                       subject2=subject2, object2=object2,
                                       type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]

    return output


def three_hop_graph_template(subject1, predicate1, object1, subject2, predicate2, object2, subject3, predicate3, object3):

    query_types = [[0, u"{subject1} {predicate1} {object1} .{subject2} {predicate2} {object2}. {subject3} {predicate3} {object3}"],
                   ]
    # could use extension
    output = [[item[0], item[1].format(predicate1=predicate1,
                                       subject1=subject1,
                                       object1=object1,
                                       predicate2=predicate2,
                                       subject2=subject2,
                                       object2=object2,
                                       predicate3=predicate3,
                                       subject3=subject3,
                                       object3=object3,
                                       type="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>")] for item in query_types]

    return output


def three_hop_graph(subject1, predicate1, object1, subject2, predicate2, object2, subject3, predicate3, object3):
    #
    graph = Graph()

    subject1 = graph.jena_formatting(subject1)
    predicate1 = graph.jena_formatting(predicate1)
    object1 = graph.jena_formatting(object1)
    subject2 = graph.jena_formatting(subject2)
    predicate2 = graph.jena_formatting(predicate2)
    object2 = graph.jena_formatting(object2)
    subject3 = graph.jena_formatting(subject3)
    predicate3 = graph.jena_formatting(predicate3)
    object3 = graph.jena_formatting(object3)
    queries = three_hop_graph_template(
        subject1, predicate1, object1, subject2, predicate2, object2, subject3, predicate3, object3)

    output = None
    if len(queries) > 0:
        # ye this might get fucked
        output = parallel_query(queries)
    # print('queries: ', queries)
    # print('output: ', output)
    return output


def two_hop_graph(subject1, predicate1, object1, subject2, predicate2, object2):
    # print('kb two_hop_graph')
    graph = Graph()

    subject1 = graph.jena_formatting(subject1)
    predicate1 = graph.jena_formatting(predicate1)
    object1 = graph.jena_formatting(object1)
    subject2 = graph.jena_formatting(subject2)
    predicate2 = graph.jena_formatting(predicate2)
    object2 = graph.jena_formatting(object2)
    queries = two_hop_graph_template(
        subject1, predicate1, object1, subject2, predicate2, object2)

    output = None
    if len(queries) > 0:
        # ye this might get fucked
        output = parallel_query(queries)
    # print('queries: ', queries)
    # print('output: ', output)
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

        # query_results[number within the template][0] = statuscode
        # query_results[number within the template][1] = response
        # query_results[number within the template][2] = q
        for i in range(len(query_results)):
            if query_results[i][0] == 200:
                results.append(
                    (query_results[i][2], query_results[i][1]["boolean"]))

        return results
