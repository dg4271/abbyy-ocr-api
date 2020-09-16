import argparse
import numpy as np
import torch
import re
import json
import sys

from torch.autograd import Variable
from torch import nn, optim
from torch.utils.data import DataLoader

sys.path.append('./table_classifier')
from dataset import SentenceClassificationDataset, preprocess, collate_fn
from preprocessing import get_input_data_new, get_header_value_info, Trie
from models import RCNN

args = argparse.ArgumentParser()
args.add_argument('--mode', type=str, default='train')
args.add_argument('--pause', type=int, default=0)
args.add_argument('--iteration', type=str, default='0')
args.add_argument('--output_size', type=int, default=1) #output label size
args.add_argument('--max_epoch', type=int, default=7)
args.add_argument('--batch', type=int, default=64)
args.add_argument('--strmaxlen', type=int, default=150)
args.add_argument('--embedding', type=int, default=300)
args.add_argument('--model_name', type=str, default='RCNN')

unit_dict = set([re.sub('\n','',unit) for unit in open('/data1/saltlux/CJPoc/table-extraction/table_classifier/unit.txt','r',encoding='utf8').readlines()])
result_check_dict = set([re.sub('\n','',unit) for unit in open('/data1/saltlux/CJPoc/table-extraction/table_classifier/result_table_dic.txt','r',encoding='utf8').readlines()])

unit_t = Trie()
for unit in unit_dict:
    unit_t.insert_string(unit)
config = args.parse_args()

def is_collect_table(raw_data, **kwargs):
  """
  : table이 제대로 detect 됐는지 분류 하는 함수
  : input = tsv 정보로 list<list>
  : output = True or False
  """
  model = RCNN(config.embedding, config.strmaxlen, config.output_size, 1150)
  criterion = nn.BCEWithLogitsLoss()
  optimizer = optim.Adam(model.parameters(), lr=0.01)
  input_data = get_input_data_new(raw_data, unit_t)
  preprocessed_data = preprocess(None, [input_data], config.strmaxlen, is_training=False)
  model.load_state_dict(torch.load("/data1/saltlux/CJPoc/table-extraction/table_classifier/model/model.pt", map_location = 'cpu'))
  model.eval()
  output_prediction = model(preprocessed_data)
  point = output_prediction.data.squeeze(dim=1).tolist()
  result = [True if re > 0.0 else False for re in point]
  return result[0]

def get_type(captions: set, row_headers :set, col_headers :set):
  """
  : 특정 테이블의 캡션, row_header, col_header정보를 이용하여 테이블의 유형을 반환하는 함수
  : input = captions :set, row_headers :set, col_headers :set, result_check_dict :set
  : output = list형식으로 genotype_table, characteristic_table, result_table의 결과
  """  
  all_info = captions | row_headers | col_headers
  result = []
  def is_genotype(all_info):
    if 'genotypes' in all_info or 'genotype' in all_info:
      return True
    else:
      return False
  
  def is_characteristic(captions):
    if 'characteristic' in captions or 'characteristics' in captions:
      return True
    else:
      return False

  def is_result(captions, result_check_dict):
    for result_checker in result_check_dict:
      for caption in captions:
        if result_checker in caption:
          return True
    return False
  
  if is_genotype(all_info):
    result.append('genotype_table')
  if is_characteristic(captions):
    result.append('characteristic_table')
  if is_result(captions, result_check_dict):
    result.append('result_table')
  return result



if __name__ == '__main__':
  """
  : table이 제대로 detect 됐는지 확인하는 테스트
  : input = tsv 정보로 list<list>
  : output = True or False
  """
  sample = []
  lines = open('./data/sample.txt', 'r', encoding='utf8').readlines()
  for line in lines:
    line = re.sub('\n','',line)
    sample.append(line.split('\t')) ## sample = list<list>
  print(is_collect_table(sample))


  """
  : table이 제대로 detect 됐는지 확인하는 테스트
  : input = tsv 정보로 list<list>
  : output = True or False
  """
  with open('./data/0001_2008_S0002929708001742_On the Replication of Genetic _001.json', 'r', encoding='utf8') as fr:
    data = json.load(fr)

  captions, row_headers, col_headers = get_header_value_info(data)
  print(get_type(captions, row_headers, col_headers, result_check_dict))