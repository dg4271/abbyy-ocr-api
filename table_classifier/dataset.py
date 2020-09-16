# -*- coding: utf-8 -*-


import os
import re
import numpy as np
from torch.utils.data import Dataset
import torch
from preprocessing import get_input_data, Trie, get_raw_input_data
import random
from utils import make_vocab


class SentenceClassificationDataset(Dataset):
    def __init__(self, dataset_path: str, max_length: int, is_training):
        """
        :param dataset_path: 데이터셋 root path
        :param max_length: 문자열의 최대 길이
        """

        self.dataset_path = dataset_path
        unit_dict = set([re.sub('\n','',unit) for unit in open('/data1/saltlux/CJPoc/table-extraction/table_classifier/unit.txt','r',encoding='utf8').readlines()])

        t = Trie()
        for unit in unit_dict:
            t.insert_string(unit)

        if is_training == 'train':

            data_list = []
            zero_data_path = os.path.join(self.dataset_path,'0')
            zero_data_list = os.listdir(zero_data_path)
            for zero_data in zero_data_list:
                with open(os.path.join(zero_data_path,zero_data),'r',encoding='utf8') as f:
                    data_list.append((get_input_data(f,t),0))
            
            one_data_path = os.path.join(self.dataset_path, '1')
            one_data_list = os.listdir(one_data_path)
            for one_data in one_data_list:
                with open(os.path.join(one_data_path,one_data),'r',encoding='utf8') as f:
                    sent = get_input_data(f, t)
                    if sent == None:
                        continue
                    data_list.append((sent,1))

            random.seed(100)
            random.shuffle(data_list)

            

            self.train_data_sentences = []
            self.train_data_labels = []
            self.test_data_sentences = []
            self.test_data_labels = []

            tot_data_len = len(data_list)
            print('total data num = {}'.format(tot_data_len))
            for idx, (sentence, label) in enumerate(data_list):
                # if idx > int(tot_data_len * 0.1):
                if idx <= int(tot_data_len):
                    self.train_data_sentences.append(sentence)
                    self.train_data_labels.append(label)
                else:
                    self.test_data_sentences.append(sentence)
                    self.test_data_labels.append(label)

            fw = open(os.path.join(self.dataset_path,'test_data'), 'w', encoding='utf8')
            for data in self.test_data_sentences:
                fw.write(data + '\n')
            fw.close()
            fw = open(os.path.join(self.dataset_path,'test_label'), 'w', encoding='utf8')
            for data in self.test_data_labels:
                fw.write(str(data) + '\n')
            fw.close()

            fw = open(os.path.join(self.dataset_path,'train_data'), 'w', encoding='utf8')
            for data in self.train_data_sentences:
                fw.write(data + '\n')
            fw.close()
            fw = open(os.path.join(self.dataset_path,'train_label'), 'w', encoding='utf8')
            for data in self.train_data_labels:
                fw.write(str(data) + '\n')
            fw.close()
            self.vocab = make_vocab(self.train_data_sentences)

            self.sentences = preprocess(self.vocab, self.train_data_sentences, max_length, True)
            self.labels = [np.float32(x) for x in self.train_data_labels]            
        else:
            self.train_data_sentences = [sent.replace('\n','') for sent in open(os.path.join(self.dataset_path,'train_data'), 'r', encoding='utf8').readlines()]
            self.train_data_labels = [label.replace('\n','') for label in open(os.path.join(self.dataset_path,'train_label'), 'r', encoding='utf8').readlines()]
            self.vocab = make_vocab(self.train_data_sentences)

            self.sentences = preprocess(self.vocab, self.train_data_sentences, max_length, False)
            self.labels = [np.float32(x) for x in self.train_data_labels]    



        print('training sentences :', len(self.sentences))

    def __len__(self):
        """
        :return: 전체 데이터의 수를 리턴합니다
        """
        return len(self.sentences)

    def __getitem__(self, idx):
        """
        :param idx: 필요한 데이터의 인덱스
        :return: 인덱스에 맞는 데이터, 레이블 pair를 리턴합니다
        """
        return self.sentences[idx], self.labels[idx]

    def get_unique_labels_num(self):
        return len(set(self.labels))

    def get_vocab_size(self):
        vocab_path = os.path.join(self.dataset_path, 'vocab.txt')
        lines = open(vocab_path, 'r', encoding='utf-8').readlines()
        return len(lines)

def preprocess(vocabs: set, data: list, max_length: int, is_training):
    """
    :param data: 문자열 리스트 ([문자열1, 문자열2, ...])
    :param max_length: 문자열의 최대 길이
    :return: 벡터 리스트 ([[0, 1, 5, 6], [5, 4, 10, 200], ...]) max_length가 4일 때
    """
    unk = 'ᴥunkᴥ'
    pad = 'ᴥpadᴥ'
    number = 'ᴥnumberᴥ'
    unit = 'ᴥunitᴥ'


    if is_training:

        vocab = {}
        vocab[pad] = 0
        vocab[unk] = 1
        vocab[number] = 2
        vocab[unit] = 3

        vocab_id = 4
        for vo in vocabs:
            vocab[vo.replace('\n', '')] = vocab_id
            vocab_id += 1        
        fw = open('/data1/saltlux/CJPoc/table-extraction/table_classifier/data/vocab.txt', 'w', encoding='utf8')

        for vo in vocab.keys():
            fw.write(vo + '\t' + str(vocab[vo]) +'\n')
        fw.close()
    else:
        vocab = {}
        fr = open('/data1/saltlux/CJPoc/table-extraction/table_classifier/data/vocab.txt', 'r', encoding='utf8')
        for line in fr.readlines():
            vo, vo_id = line.split('\t')
            vocab[vo] = int(vo_id.replace('\n',''))
        
    vectorized_data = []
    for datum in data:
        sent = datum.replace('\n', '').replace('\r', '')
        vec = []
        for token in sent.split(' '):
            if token in vocab.keys():
                vec.append(vocab[token])
            else:
                vec.append(vocab[unk])
        vectorized_data.append(vec)

    zero_padding = np.zeros((len(data), max_length), dtype=np.int)
    for idx, seq in enumerate(vectorized_data):
        length = len(seq)
        if length >= max_length:
            length = max_length
            zero_padding[idx, :length] = np.array(seq)[:length]
        else:
            zero_padding[idx, :length] = np.array(seq)
    return zero_padding



def collate_fn(data: list):
    """
    :param data: 데이터 리스트
    :return:
    """
    sentences = []
    label = []
    for datum in data:
        sentences.append(datum[0])
        label.append(datum[1])

    # sent2tensor = torch.tensor(sentences, device='cuda' if torch.cuda.is_available() else 'cpu', dtype=torch.long)
    # label2tensor = torch.tensor(label, device='cuda' if torch.cuda.is_available() else 'cpu', dtype=torch.long)
    sent2tensor = torch.tensor(sentences, device ='cpu', dtype=torch.long)
    label2tensor = torch.tensor(label, device='cpu', dtype=torch.long)
    
    return sent2tensor, label2tensor



if __name__ == '__main__':
    data_list = []
    zero_data_path = os.path.join('./data','0')
    zero_data_list = os.listdir(zero_data_path)
    fw = open('./data/raw_data', 'w', encoding='utf8') 
    for zero_data in zero_data_list:
        with open(os.path.join(zero_data_path,zero_data),'r',encoding='utf8') as f:
            fw.write(get_raw_input_data(f) + '\t' + '0' + '\n')
            


    one_data_path = os.path.join('./data', '1')
    one_data_list = os.listdir(one_data_path)
    for one_data in one_data_list:
        with open(os.path.join(one_data_path,one_data),'r',encoding='utf8') as f:
            sent = get_raw_input_data(f)
            if sent == None:
                continue
            fw.write(sent + '\t' + '1' + '\n')
    fw.close()