import json
#import nntplib
import os
import numpy as np
import torch.nn as nn
import torch
from common.graph.graph import Graph
from common.query.querybuilder import QueryBuilder
from complex_queries import mutli_var_complex_query
import kb
from learning.treelstm import Constants, preprocess_lcquad
from learning.treelstm.dataset import QGDataset
from learning.treelstm.model import DASimilarity, SimilarityTreeLSTM
from learning.treelstm.trainer import Trainer
from learning.treelstm.vocab import Vocab
import torch.optim as optim
from myclassifier import QuestionClassifier
from parser.lc_quad import LC_Qaud, LC_QaudParser
from parser.lc_quad_linked import LC_Qaud_LinkedParser
from svmclassifier import SVMClassifier
import ujson

class Struct(object): pass

def rank(args, question, generated_queries):
        #print("We are in rank and this is the params:",args, question, generated_queries)
        if len(generated_queries) == 0:
            return []
        if True:
            # try:
            # Load the model
            if not os.path.exists(args.save):
                os.makedirs(args.save)
            checkpoint_filename = os.path.join(args.save, '%s.pt' % args.expname)

            #checkpoint_filename = '%s.pt' % os.path.join(args.save, args.expname)
            #dataset_vocab_file is like city,did,direct,director,ent
            dataset_vocab_file = os.path.join(args.data, 'dataset.vocab')
            # metrics = Metrics(args.num_classes)
            vocab = Vocab(filename=dataset_vocab_file,
                          data=[Constants.PAD_WORD, Constants.UNK_WORD, Constants.BOS_WORD, Constants.EOS_WORD])
            
            similarity = DASimilarity(args.mem_dim, args.hidden_dim, args.num_classes)
            
            model = SimilarityTreeLSTM(
                vocab.size(),
                args.input_dim,
                args.mem_dim,
                similarity,
                args.sparse)
            criterion = nn.KLDivLoss()
            optimizer = optim.Adagrad(model.parameters(), lr=args.lr, weight_decay=args.wd)
            #print("this is optimizer" ,optimizer)
            emb_file = os.path.join(args.data, 'dataset_embed.pth')
            #print(emb_file)
            if os.path.isfile(emb_file):
                emb = torch.load(emb_file)
            #print(model.emb.weight.data.copy_(emb))
            model.emb.weight.data.copy_(emb)

            

            checkpoint = torch.load(checkpoint_filename, map_location=lambda storage, loc: storage)
            #print("this is checkpoint",checkpoint_filename)
            model.load_state_dict(checkpoint['model'])
            trainer = Trainer(args, model, criterion, optimizer)
            #print()
            generated_queries_sparql = generated_queries[1::2]
            #print(generated_queries_sparql)
            generated_queries = generated_queries[0::2]
            #print(generated_queries)
            #print()
            # Prepare the dataset with the sparql queries and not the natural lang questions
            json_data = [{"id": "test", "question": question,
                          "generated_queries": [{"query": query, "correct": False} for query in
                                                generated_queries_sparql]}]
            #print(json_data)
            parser = LC_Qaud_LinkedParser()
            output_dir = "./output/tmp"
            
            #we need to fix this, it is fucked
            preprocess_lcquad.save_split(output_dir, *preprocess_lcquad.split(json_data, parser))
            #preprocess_lcquad.correct_data(generated_queries)

            dep_tree_cache_file_path = './json_files/dep_tree_cache_lcquadtest.json'
            if os.path.exists(dep_tree_cache_file_path):
                with open(dep_tree_cache_file_path) as f:
                    dep_tree_cache = ujson.load(f)
            else:
                dep_tree_cache = dict()

            if question in dep_tree_cache:
                #print(question)
                
                preprocess_lcquad.parse(output_dir, dep_parse=False)

                cache_item = dep_tree_cache[question]
                with open(os.path.join(output_dir, 'a.parents'), 'w') as f_parent, open(
                        os.path.join(output_dir, 'a.toks'), 'w') as f_token:
                   
                    for i in range(len(generated_queries)):
                        f_token.write(cache_item[0])
                        f_parent.write(cache_item[1])

                    
            else:
                preprocess_lcquad.parse(output_dir)
                with open(os.path.join(output_dir, 'a.parents')) as f:
                    parents = f.readline()
                with open(os.path.join(output_dir, 'a.toks')) as f:
                    print("this is token",f.readline())
                    tokens = f.readline()
                
                dep_tree_cache[question] = [tokens, parents]

                with open(dep_tree_cache_file_path, 'w') as f:
                    ujson.dump(dep_tree_cache, f)
            
            
            test_dataset = QGDataset(output_dir, vocab, args.num_classes)
            print("length of dataset" ,len(test_dataset))

            test_loss, test_pred = trainer.test(test_dataset)
            return test_pred
        # except Exception as expt:
        #     self.logger.error(expt)
        #     return []


def generate_query(question, entities, relations, h1_threshold=9999999, question_type=2):
    ask_query = False
    sort_query = False
    count_query = False

    if question_type == 2:
        count_query = True
    elif question_type == 1:
        ask_query = True

    '''type_confidence = question_type_classifier.predict_proba([question])[0][question_type]
    if isinstance(QuestionClassifier.predict_proba([question])[0][question_type], (np.ndarray, list)):
        type_confidence = type_confidence[0]'''
    
    #question_type_classifier = SVMClassifier("question_type_classifier/svm.model")
    double_relation_classifier = SVMClassifier("/home/bell/rdf_code/question_type_classifier/svm.model")
    double_relation = False
    if double_relation_classifier is not None:
        double_relation = double_relation_classifier.predict([question])
        print("this is our double relation classifier, 1 is double relations",double_relation_classifier.predict([question]))
        if double_relation == 1:
            double_relation = True
        
        #i dont think we can use svm models build on other data??? 
        #it is throwing errors like crazy too 
    double_relation = True
    graph = Graph()
    #print(graph)
    query_builder = QueryBuilder()
    #print(query_builder)

    #I think this is where we need to focus
    graph.find_minimal_subgraph(entities, relations, double_relation=double_relation, ask_query=ask_query,
                                sort_query=sort_query, h1_threshold=h1_threshold)
    #multi_var_queries= graph.mutli_var_complex_query(graph.edges)
    valid_walks_with_sparql = query_builder.to_where_statement(graph, ask_query=ask_query,
                                                    count_query=count_query, sort_query=sort_query)
    #print("these are the valid paths found:" ,valid_walks_with_sparql)

    #use these valid paths to combine to multi var to check if <path1><path2> works within a query, (what I call double relation)

    complex_walks = mutli_var_complex_query(valid_walks_with_sparql)
    
    #print()
    #print("this is complex walk",complex_walks)
    #print()
    for array_with_walks in complex_walks:
        for walk in array_with_walks:
            #print(walk)
            valid_walks_with_sparql.append(walk)
    #print(valid_walks_with_sparql)
    #print("these are the valid paths with more complex queries found:" ,valid_walks_with_sparql)

    

    
    #I DONT UNDERSTAND WHY WE ARE DOING THIS 

    if question_type == 0 and len(relations) == 1:
        double_relation = True
        graph = Graph()
        query_builder = QueryBuilder()
        graph.find_minimal_subgraph(entities, relations, double_relation=double_relation, ask_query=ask_query,
                                    sort_query=sort_query, h1_threshold=h1_threshold)
        valid_walks_new = query_builder.to_where_statement(graph,
                                                            ask_query=ask_query,
                                                            count_query=count_query, sort_query=sort_query)
        
        valid_walks_with_sparql.extend(valid_walks_new)

    args = Struct()
    base_path = "./learning/treelstm/"
    args.save = os.path.join(base_path, "checkpoints/")
    #changed the checkpoint_filename from lc_quad,epoch=5,train_loss=0.08340245485305786
    args.expname = "lc_quad,epoch=5,train_loss=0.07691806554794312"
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
    #try:
    #we need to include the full where, so it becomes like SELECT * ... - fixed
    #try:
    scores = rank(args, question, valid_walks_with_sparql)
    print("The try worked, this is the scores:",scores)
        
    '''except:
        scores = [1 for _ in valid_walks_with_sparql]
        print("The try DIDNT worked, this is the scores:",scores)'''
    
    #trim the valid_walks_with_sparql so it only includes SELECT * where... 
    valid_walks_with_sparql =valid_walks_with_sparql[1::2]
    
    valid_walks_dicts = {}
    all_valid_walks= []
    for query in valid_walks_with_sparql:
        if query not in [item["query"] for item in all_valid_walks]:
            valid_walks_dicts = {"query": query}
            all_valid_walks.append(valid_walks_dicts)

    
    #print(all_valid_walks)
    #valid_walks_with_sparql = [json.loads(s) for s in valid_walks_with_sparql]
            
    for idx, item in enumerate(all_valid_walks):
        #print("We are in the for loop",idx,item)
        #If the index is larger than the lenght of the scores???????
        if idx >= len(scores):
            #hardcode
            item["confidence"] = 0.3
        else:
            #print("this is scores[idx]",scores[idx]) 
            item["confidence"] = float(scores[idx] - 1)
    
    item_with_highest_confidence = max(all_valid_walks, key=lambda x: x["confidence"])
    
    return item_with_highest_confidence
    
    #print("this is the valid walks when we are done",all_valid_walks)

   