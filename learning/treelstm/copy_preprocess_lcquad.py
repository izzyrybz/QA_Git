import os
import sys
import glob
import json
import anytree
from tqdm import tqdm
import sys
import requests
import spacy
path = os.getcwd()
sys.path.insert(0, path)
from common.utility.utility import find_mentions
from parser.lc_quad_linked import LC_Qaud_LinkedParser
# sys.path.append('/cluster/home/xlig/kg/')
# sys.path.insert(0, '/cluster/home/xlig/kg/')

def contains_ent(string):
    return "#ent" in string
    
'''def contains_fucked_ent(string):
    if ("#entt" in string):
        string = string.replace("#entt", "#ent")        
        return string
    else:
        return string'''


def generalize_question(question, sparql_query, parser=None):
    if parser is None:
        parser = LC_Qaud_LinkedParser()
    
    #question= contains_fucked_ent(question)
    
    if(contains_ent(question)):
        print("contains ent",question)
        #if the question contains #ent we have already processed it
        # Remove extra info from the relation's URI and remaining entities
        prefixes = ["http://dbpedia.org/resource/", "http://dbpedia.org/ontology/",
                    "http://dbpedia.org/property/", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"]
        for prefix in prefixes:
            sparql_query = sparql_query.replace(prefix, "")
        sparql_query = sparql_query.replace("<", "").replace(">", "")

        return question, sparql_query
        
    else:
        print("contains no ent",question)

        # Extract URIs from the SPARQL query
        _, _, uris = parser.parse_sparql(sparql_query)

        # Replace entity mentions in question with generic symbols
        entity_symbols = {}
        #print("we have found this uri within the question",find_mentions(question, uris))
        for item in find_mentions(question, uris):
            
            uri = item["uri"]
            #print("we are now working with ",uri)
            if uri in entity_symbols:
                #print("uri is in entity symbols",symbol)
                symbol = entity_symbols[uri]
            else:
                #print("uri is NOT in entity symbols")
                i = len(entity_symbols) + 1
                #print("we have now taken the length of this",entity_symbols)
                symbol = "t" * i
                #print("t*i , wtf",symbol)
                entity_symbols[uri] = symbol
                #print(entity_symbols[uri])
            question = "{} #en{} {}".format(question[:item["start"]], symbol, question[item["end"]:])
            sparql_query = sparql_query.replace(uri, "#" + symbol)

        # Remove extra info from the relation's URI and remaining entities
        prefixes = ["http://dbpedia.org/resource/", "http://dbpedia.org/ontology/",
                    "http://dbpedia.org/property/", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"]
        for prefix in prefixes:
            sparql_query = sparql_query.replace(prefix, "")
        sparql_query = sparql_query.replace("<", "").replace(">", "")

        return question, sparql_query



def make_dirs(dirs):
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)


def dependency_parse(filepath):
    spacy.prefer_gpu()
    nlp = spacy.load("en_core_web_lg")

    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    tokpath = os.path.join(dirpath, filepre + '.toks')
    parentpath = os.path.join(dirpath, filepre + '.parents')
    relpath = os.path.join(dirpath, filepre + '.rels')
    pospath = os.path.join(dirpath, filepre + '.pos')
    tagpath = os.path.join(dirpath, filepre + '.tag')
    lenpath = os.path.join(dirpath, filepre + '.len')

    with open(tokpath, 'w', encoding='utf-8') as tokfile, \
            open(relpath, 'w', encoding='utf-8') as relfile, \
            open(parentpath, 'w', encoding='utf-8') as parfile, \
            open(lenpath, 'w', encoding='utf-8') as lenfile, \
            open(tagpath, 'w', encoding='utf-8') as tagfile, \
            open(pospath, 'w', encoding='utf-8') as posfile:
        with open(os.path.join(dirpath, 'a.txt'), 'r', encoding='utf-8') as f:
            for line in f:
                l = line.split(' ')
                l = [i for i in l if i != '']
                newline = ' '.join(l)
                doc = nlp(newline)
                json_doc = doc.to_json()
                token = json_doc['tokens']
                pos = []
                tag = []
                dep = []
                tok = []
                parent = []
                length = json_doc['sents'][0]['end'] + 1
                for t in token:
                    if t['pos'] != 'SPACE':
                        tok.append(doc[t['id']].text)
                        pos.append(t['pos'])
                        tag.append(t['tag'])
                        dep.append(t['dep'])
                        head = t['head']
                        if t['dep'] == 'ROOT':
                            head = 0
                        else:
                            head = head + 1
                        parent.append(head)
                tokfile.write(' '.join(tok) + '\n')
                posfile.write(' '.join(pos) + '\n')
                tagfile.write(' '.join(tag) + '\n')
                relfile.write(' '.join(dep) + '\n')
                parfile.writelines(["%s " % str(item) for item in parent])
                parfile.write('\n')
                lenfile.write(str(length) + '\n')


def query_parse(filepath):
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    tokpath = os.path.join(dirpath, filepre + '.toks')
    parentpath = os.path.join(dirpath, filepre + '.parents')
    with open(filepath) as datafile, \
            open(tokpath, 'w') as tokfile, \
            open(parentpath, 'w') as parentfile:
        for line in tqdm(datafile):
            clauses = line.split(" .")
            vars = dict()
            root = None
            for clause in clauses:
                triple = [item.replace("\n", "") for item in clause.split(" ")]

                root_node = anytree.Node(triple[1])
                left_node = anytree.Node(triple[0], root_node)
                right_node = anytree.Node(triple[2], root_node)

                leveled = [left_node, root_node, right_node]
                for item in triple:
                    if item.startswith("?u_"):
                        if item in vars:
                            children = vars[item].parent.children
                            if children[0] == vars[item]:
                                vars[item].parent.children = [root_node, children[1]]
                            else:
                                vars[item].parent.children = [children[0], root_node]
                            vars[item] = [node for node in leveled if node.name == item][0]
                            break
                        else:
                            vars[item] = [node for node in leveled if node.name == item][0]

                if root is None:
                    root = root_node

            pre_order = [node for node in anytree.iterators.PreOrderIter(root)]
            tokens = [node.name for node in pre_order]
            for i in range(len(pre_order)):
                pre_order[i].index = i + 1
            idxs = [node.parent.index if node.parent is not None else 0 for node in pre_order]

            tokfile.write(" ".join(tokens) + "\n")
            parentfile.write(" ".join(map(str, idxs)) + "\n")


def build_vocab(filepaths, dst_path, lowercase=True):
    vocab = set()
    for filepath in filepaths:
        with open(filepath) as f:
            for line in f:
                if lowercase:
                    line = line.lower()
                vocab |= set(line.split())
    with open(dst_path, 'w') as f:
        for w in sorted(vocab):
            f.write(w + '\n')


def is_entity_dbpedia(uri):
    # Define the DBpedia endpoint URL and query
    try:
        dbpedia_endpoint = "http://dbpedia.org/sparql"
        dbpedia_query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?label WHERE {
                """ + uri + """ rdf:type ?type .
                ?type rdfs:subClassOf* <http://dbpedia.org/ontology/Entity> .
                """ + uri + """ rdfs:label ?label .
                FILTER (lang(?label) = 'en')
            }
            LIMIT 1
        """

        # Send the query to DBpedia using the requests library
        response = requests.get(dbpedia_endpoint, params={'query': dbpedia_query})
        if response.status_code == 200:
            result = response.json()['results']['bindings']
            if len(result) > 0:
                label = result[0]['label']['value']
                return True
    except:
        return False


def is_entity(uri):
    # check dbpedia
    print("this is the uri we are working with",uri)
    if(is_entity_dbpedia(uri)):
        return True
    #check if it is ?uri
    elif uri.startswith("?"):
        return True
    
    elif uri.startswith("'"):
        return True
    else:
        return False


'''def generalize_question(question, sparql_query, parser=None):
    a =question
    b =sparql_query 
    # replace entity mention in question with a generic symbol
    #print("we are in generalize_question, a ,b ", a ,b)

    if parser is None:
        parser = LC_Qaud_LinkedParser()

    
    _, _, uris = parser.parse_sparql(b)
    #this is then the response from the sparql query
    #print(_, _, uris)

    #WE POSSIBLY HAVE PROBLEM HERE

    #uris = [uri for uri in uris if is_entity(uri)]

    i = 0
    # if the question is in the answer
    for item in find_mentions(a, uris):
        a = "{} #en{} {}".format(a[:item["start"]], "t" * (i + 1), a[item["end"]:])
        #print("we are inside item",a,item,uris)
        b = b.replace(item["uri"], "#en{}".format("t" * (i + 1)))
        
    # remove extra info from the relation's uri and remaining entities
    for item in ["http://dbpedia.org/resource/", "http://dbpedia.org/ontology/",
                 "http://dbpedia.org/property/", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"]:
        b = b.replace(item, "")
    b = b.replace("<", "").replace(">", "")

    #print("We are done with generalization",a,b)

    return a, b'''


def split(data, parser=None):
    if isinstance(data, str):
        with open(data) as datafile:
            dataset = json.load(datafile)
    else:
        dataset = data

    a_list = []
    b_list = []
    id_list = []
    sim_list = []
    for item in tqdm(dataset):
        i = item["id"]
        a = item["question"]
        #print("started tqdm",i,a)
        for query in item["generated_queries"]:
            a, b = generalize_question(a, query["query"], parser)
            #print()

            # Empty query should be ignored
            if len(b) < 5:
                continue
            sim = str(2 if query["correct"] else 1)

            id_list.append(i + '\n')
            a_list.append(a.encode('ascii', 'ignore').decode('ascii') + '\n')
            b_list.append(b.encode('ascii', 'ignore').decode('ascii') + '\n')
            sim_list.append(sim + '\n')
    
        # Convert the array to a set to remove duplicates
    '''unique_set = set(a_list)
    [unique_set.append(x) for x in unique_set if x not in unique_set]

    # Convert the set back to a list
    a_list = list(unique_set)'''

    
    #print("we are in preprocess",a_list,b_list,id_list)
    return a_list, b_list, id_list, sim_list


def save_split(dst_dir, a_list, b_list, id_list, sim_list):
    with open(os.path.join(dst_dir, 'a.txt'), 'w') as afile, \
            open(os.path.join(dst_dir, 'b.txt'), 'w') as bfile, \
            open(os.path.join(dst_dir, 'id.txt'), 'w') as idfile, \
            open(os.path.join(dst_dir, 'sim.txt'), 'w') as simfile:
        for i in range(len(a_list)):
            idfile.write(id_list[i])
            afile.write(a_list[i])
            bfile.write(b_list[i])
            simfile.write(sim_list[i])


def parse(dirpath, dep_parse=True):
    if dep_parse:
        dependency_parse(os.path.join(dirpath, 'a.txt'))
    query_parse(os.path.join(dirpath, 'b.txt'))


if __name__ == '__main__':
    print('=' * 80)
    print('Preprocessing LC-Quad dataset')
    print('=' * 80)

    base_dir = os.path.dirname(os.path.realpath(__file__))
    print('base_dir: ', base_dir)
    data_dir = os.path.join(base_dir, 'data')
    lc_quad_dir = os.path.join(data_dir, 'lc_quad')
    lib_dir = os.path.join(base_dir, 'lib')
    train_dir = os.path.join(lc_quad_dir, 'train')
    dev_dir = os.path.join(lc_quad_dir, 'dev')
    test_dir = os.path.join(lc_quad_dir, 'test')
    make_dirs([train_dir, dev_dir, test_dir])

    # split into separate files
    train_filepath = os.path.join(lc_quad_dir, 'LCQuad_train.json')
    trail_filepath = os.path.join(lc_quad_dir, 'LCQuad_trial.json')
    test_filepath = os.path.join(lc_quad_dir, 'LCQuad_test.json')

    ds = json.load(open("json_files/gold.json"))

    total = len(ds)
    train_size = int(.7 * total)
    dev_size = int(.2 * total)
    test_size = int(.1 * total)
    print('Totle: ', total)
    print('train_size: ', train_size)
    print('dev_size: ', dev_size)
    print('test_size: ', test_size)

    json.dump(ds[:train_size], open(train_filepath, "w"))
    json.dump(ds[train_size:train_size + dev_size], open(trail_filepath, "w"))
    json.dump(ds[train_size + dev_size:], open(test_filepath, "w"))

    parser = LC_Qaud_LinkedParser()

    print('Split train set')
    save_split(train_dir, *split(train_filepath, parser))
    print('Split dev set')
    save_split(dev_dir, *split(trail_filepath, parser))
    print('Split test set')
    save_split(test_dir, *split(test_filepath, parser))

    # parse sentences
    print("parse train set")
    parse(train_dir)
    print("parse dev set")
    parse(dev_dir)
    print("parse test set")
    parse(test_dir)

    # get vocabulary
    build_vocab(
        glob.glob(os.path.join(lc_quad_dir, '*/*.toks')),
        os.path.join(lc_quad_dir, 'vocab.txt'))
    build_vocab(
        glob.glob(os.path.join(lc_quad_dir, '*/*.toks')),
        os.path.join(lc_quad_dir, 'vocab-cased.txt'),
        lowercase=False)