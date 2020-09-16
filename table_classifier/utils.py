import requests
import os
import re
import json
import random
from preprocessing import cleansing_sentence

def count_token(lines):
  token2count = dict()
  for line in lines:
    line = cleansing_sentence(line)
    tokens = line.split(' ')
    for token in tokens:
      token = token.lower()
      if token in token2count:
        token2count[token] += 1
      else:
        token2count[token] = 1
  result = sorted(token2count.items(), key=lambda x: x[1], reverse=True)
  return result
    
def make_vocab(data_list, min_count = 10):

  vocab_set = set()
  vocab_num = dict()

  for data in data_list:
    for token in data.split(' '):
      if token not in vocab_num:
        vocab_num[token] = 1
      else:
        ori_num = vocab_num[token]
        ori_num += 1
        vocab_num[token] = ori_num        

    for vocab in vocab_num:
      if vocab_num[vocab] > min_count:
        vocab_set.add(vocab)


  return vocab_set
  

@staticmethod
def topk_accuracy(proba, true_labels, k):
  topk_labels = (-proba).argsort()[:, :k]
  total = proba.shape[0]
  n_correct = 0
  for p, topk in zip(true_labels, topk_labels):
    if p in topk: n_correct += 1
  score = n_correct / total
  print("accuracy@top{}: {}".format(k, score))
  return score



if __name__ == '__main__':
  # data = []
  # data.extend(open('./nutri_caption.txt','r',encoding='utf8').readlines())
  # data.extend(open('./metabolic_caption.txt','r',encoding='utf8').readlines())
  # token2count = count_token(data)

  # f = open('token_count.txt' ,'w', encoding='utf8')
  # for (token, count) in token2count:
  #   f.write(token + '\t' + str(count) + '\n')
  # f.close()
  unit = set()
  lines = open('./unit_dict.txt','r',encoding='utf8').readlines()
  for line in lines:
    unit.add(re.sub('\n','',line))
  writer = open('./unit.txt','w',encoding='utf8')
  for u in unit:
    writer.write(u + '\n')
  writer.close()

