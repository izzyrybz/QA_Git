from tqdm import tqdm

import torch
from torch.autograd import Variable as Var
from torch.utils.data import DataLoader

from learning.treelstm.utils import map_label_to_target
import numpy as np
from numpy.linalg import norm

def cosine_similarity(tensor1, tensor2):
    max_size = max(tensor1.size(0), tensor2.size(0))
    padded_tensor1 = torch.zeros(max_size)
    padded_tensor2 = torch.zeros(max_size)
    padded_tensor1[:tensor1.size(0)] = tensor1
    padded_tensor2[:tensor2.size(0)] = tensor2
    return torch.nn.functional.cosine_similarity(padded_tensor1, padded_tensor2, dim=0)



class Trainer(object):
    def __init__(self, args, model, criterion, optimizer):
        super(Trainer, self).__init__()
        self.args = args
        self.model = model
        self.criterion = criterion
        self.optimizer = optimizer
        self.epoch = 0

    # helper function for training
    def train(self, dataset):
        #print("we are now training")
        self.model.train()
        self.optimizer.zero_grad()
        loss, k = 0.0, 0
        indices = torch.randperm(len(dataset))
        for idx in tqdm(range(len(dataset)), desc='Training epoch ' + str(self.epoch + 1) + ''):
            ltree, lsent, rtree, rsent, label = dataset[indices[idx]]
            #print(ltree, lsent, rtree, rsent)
            linput, rinput = Var(lsent), Var(rsent)
            target = Var(map_label_to_target(label, dataset.num_classes))
            if self.args.cuda:
                linput, rinput = linput.cuda(), rinput.cuda()
                target = target.cuda()
            output = self.model(ltree, linput, rtree, rinput)
            err = self.criterion(output, target)
            loss += err.item()
            err.backward()
            k += 1
            if k % self.args.batchsize == 0:
                self.optimizer.step()
                self.optimizer.zero_grad()
        self.epoch += 1
        return loss / len(dataset)





    # helper function for testing
    def test(self, dataset):
        #for data in dataset:
            #print("this is our data",data)
        self.model.eval()
        
        
        #print(self.model)
        loss = 0
        predictions = torch.zeros(len(dataset))
        indices = torch.arange(1, dataset.num_classes + 1, dtype=torch.float)
        for idx in tqdm(range(len(dataset)), desc='Testing epoch  ' + str(self.epoch) + ''):
            ltree, lsent, rtree, rsent, label = dataset[idx]

            
            #lsent, rsent,label are tensors that does have anything to do with the output
            
            #print("TREE",ltree.children, lsent, rtree.children, rsent, label)
            

            linput, rinput = Var(lsent), Var(rsent)
            #print("input",linput,rinput)
            target = Var(map_label_to_target(label, dataset.num_classes))
            
            if self.args.cuda:
                linput, rinput = linput.cuda(), rinput.cuda()
                target = target.cuda()
            
            #linput = torch.tensor(x)
            #print("this is our ltree, linput, rtree, rinput",ltree, linput, rtree, rinput)
            
            output = self.model(ltree, linput, rtree, rinput)
            
            err = self.criterion(output, target)
            loss += err.data
            
            output = output.data.squeeze().cpu()
            
            predictions[idx] = torch.dot(indices, torch.exp(output))
            '''if cosine_similarity(linput,rinput) is not None:
                
                predictions[idx] = cosine_similarity(linput,rinput)
                print("looked at ",linput,rinput,cosine_similarity(linput,rinput))'''
            
            
        if len(dataset)== 0:
            print("we have 0??")
            exit()
            return 0,predictions
        else:
            return loss / len(dataset), predictions
