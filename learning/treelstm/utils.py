from __future__ import division
from __future__ import print_function

import os
import math

import torch

from learning.treelstm.tree import Tree
from learning.treelstm.vocab import Vocab


# loading GLOVE word vectors
# if .pth file is found, will load that
# else will load from .txt file & save
def load_word_vectors(path):
    if os.path.isfile(path + '.pth') and os.path.isfile(path + '.vocab'):
        print('==> File found, loading to memory')
        vectors = torch.load(path + '.pth')
        vocab = Vocab(filename=path + '.vocab')
        return vocab, vectors
    # saved file not found, read from txt file
    # and create tensors for word vectors
    print('==> File not found, preparing, be patient')
    count = sum(1 for line in open(path + '.txt', encoding='utf-8', errors='ignore'))
    with open(path + '.txt', 'r') as f:
        contents = f.readline().rstrip('\n').split(' ')
        dim = len(contents[1:])
    words = [None] * (count)
    vectors = torch.zeros(count, dim)
    with open(path + '.txt', 'r', encoding='utf-8', errors='ignore') as f:
        idx = 0
        for line in f:
            contents = line.rstrip('\n').split(' ')
            words[idx] = contents[0]
            vectors[idx] = torch.Tensor(list(map(float, contents[1:])))
            idx += 1
    with open(path + '.vocab', 'w', encoding='utf-8', errors='ignore') as f:
        for word in words:
            f.write(word + '\n')
    vocab = Vocab(filename=path + '.vocab')
    torch.save(vectors, path + '.pth')
    return vocab, vectors


# write unique words from a set of files to a new file
def build_vocab(filenames, vocabfile):
    vocab = set()
    for filename in filenames:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for line in f:
                    tokens = line.rstrip('\n').split(' ')
                    new_tokens=[]
                    for token in tokens:
                        
                        if('http://example.org/ontology/' in token):
                            print("we go into the if statment")
                            token = token.replace('http://example.org/ontology/','')
                            token = token.replace('<','')
                            token = token.replace('>','')
                            new_tokens.append(token)
                        elif('http://example.org/action/' in token):
                            token = token.replace('http://example.org/action/','')
                            token = token.replace('<','')
                            token = token.replace('>','')
                            new_tokens.append(token)
                        elif('http://example.org/entity/' in token):
                            token = token.replace('http://example.org/entity/','')
                            token = token.replace('<','')
                            token = token.replace('>','')
                            new_tokens.append(token)
                        else:
                            new_tokens.append(token)

                    #print("this is old",tokens)
                    #print("this is new",new_tokens)
                    
                        
                    vocab |= set(new_tokens)
    with open(vocabfile, 'w') as f:
        for token in sorted(vocab):
            f.write(token + '\n')


# mapping from scalar to vector
def map_label_to_target(label, num_classes):
    target = torch.zeros(1, num_classes)
    
    ceil = int(math.ceil(label))
    floor = int(math.floor(label))
    if ceil == floor:
        target[0][floor - 1] = 1
    else:
        target[0][floor - 1] = ceil - label
        target[0][ceil - 1] = label - floor
    return target
