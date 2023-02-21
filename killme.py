import numpy as np
from common.graph.graph import Graph

from common.query.querybuilder import QueryBuilder
import kb
from myclassifier import QuestionClassifier
import parser
from svmclassifier import SVMClassifier

class Struct(object): pass

def generate_query(question, entities, relations, h1_threshold=9999999, question_type=2):
    ask_query = False
    sort_query = False
    count_query = False

    if question_type == 2:
        count_query = True
    elif question_type == 1:
        ask_query = True

    '''type_confidence = question_classifier.predict_proba([question])[0][question_type]
    if isinstance(QuestionClassifier.predict_proba([question])[0][question_type], (np.ndarray, list)):
        type_confidence = type_confidence[0]
    '''
    question_type_classifier = SVMClassifier("double_relation_classifier/svm.model")
    double_relation_classifier = SVMClassifier("/home/bell/rdf_code/question_type_classifier/svm.model")
    double_relation = False
    if double_relation_classifier is not None:
        double_relation = double_relation_classifier.predict([question])
        print(double_relation_classifier.predict([question]))
        if double_relation == 1:
            double_relation = True

    graph = Graph(kb)
    query_builder = QueryBuilder()
    #I think this is where we need to focus
    graph.find_minimal_subgraph(entities, relations, double_relation=double_relation, ask_query=ask_query,
                                sort_query=sort_query, h1_threshold=h1_threshold)

    valid_walks = query_builder.to_where_statement(graph, parser.parse_queryresult, ask_query=ask_query,
                                                    count_query=count_query, sort_query=sort_query)

    if question_type == 0 and len(relations) == 1:
        double_relation = True
        graph = Graph()
        query_builder = QueryBuilder()
        graph.find_minimal_subgraph(entities, relations, double_relation=double_relation, ask_query=ask_query,
                                    sort_query=sort_query, h1_threshold=h1_threshold)
        valid_walks_new = query_builder.to_where_statement(graph, parser.parse_queryresult,
                                                            ask_query=ask_query,
                                                            count_query=count_query, sort_query=sort_query)
        valid_walks.extend(valid_walks_new)

    args = Struct()
    base_path = "./learning/treelstm/"
    args.expname = "lc_quad,epoch=5,train_loss=0.08340245485305786"
    args.mem_dim = 150
    args.hidden_dim = 50
    args.num_classes = 2
    args.input_dim = 300
    args.sparse = False
    args.lr = 0.01
    args.wd = 1e-4
    args.data = os.path.join(base_path, "data/lc_quad/")
    args.cuda = False
    # args.cuda = True
    '''try:
        scores = rank(args, question, valid_walks)
    except:
        scores = [1 for _ in valid_walks]
    for idx, item in enumerate(valid_walks):
        if idx >= len(scores):
            item["confidence"] = 0.3
        else:
            item["confidence"] = float(scores[idx] - 1)
'''
    print(valid_walks, question_type)

question = "Which commits have the user izzyrybz made?"
entities = [
            {
                "confidence": 0.9239816818240237,
                "uri": "http://dbpedia.org/resource/Commit_(version_control)"
            },
    
            {
                "confidence": 0.9170735543251727,
                "uri": "http://dbpedia.org/resource/User_interface"
            },

            {
                "confidence": 0.8956483894223672,
                "uri": "http://dbpedia.org/resource/Langues_d'o\u00efl"
            },
        
            {
                "confidence": 0.75,
                "uri": "izzyrybz"
            }]
h1_threshold = 9999999
relations = [
            {
                "confidence": 0.75,
                "uri": "https://dbpedia.org/ontology/author"
            },

            {
                "confidence": 0.75,
                "uri": "https://dbpedia.org/ontology/Description"
            },

            
            {
                "confidence": 0.5,
                "uri": "https://dbpedia.org/ontology/author"
            },
           
            {
                "confidence": 0.5,
                "uri": "https://dbpedia.org/property/user"
            }
                
]
generate_query(question,entities,relations,h1_threshold,question_type=2)