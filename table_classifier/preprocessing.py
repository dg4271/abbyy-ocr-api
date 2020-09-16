import re

# unit_set = set()

# for line in open('', 'r', encoding='utf8').readlines():
#   unit_set.add(re.sub('\n','',line))


def get_raw_input_data(f):
  input_data = []
  
  try:
    for line in f.readlines():
      line = re.sub('\n','', line)
      if is_caption(line):
        continue
      else:
        line = re.sub('<br>','', line)
        input_data.append(re.sub('\t', ' ',line))
    return ' '.join(input_data)
  except:
    return None    


def get_input_data(f, dic):
  input_data = []
  try:
    for line in f.readlines():
      if is_caption(line):
        continue
      else:
        input_data.append(cleansing_sentence(line, dic))
    return ' '.join(input_data)
  except:
    return None    

def get_input_data_new(table, dic):
  input_data = []
  try:
    for tokens in table:
      line = '\t'.join(tokens)
      if is_caption(line):
        continue
      else:
        input_data.append(cleansing_sentence(line, dic))
    return ' '.join(input_data)
  except:
    return None
    
def cleansing_sentence(line, dic):
  line = re.sub('<br>', '', line)
  line = re.sub('<srow>', '', line)
  line = re.sub('</srow>', '', line)
  line = re.sub('<indent>', '', line)
  line = re.sub('<ssrow>', '', line)
  line = re.sub('</ssrow>', '', line)
  line = re.sub('\t',' ᴥtabᴥ ', line)
  line = unit_processing(line, dic)
  line = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!『』;（）{}。、\\‘|\(\)\[\]\>\<`\'…》±]', '', line) ## <> 이거를 어떡할까나
  line = re.sub('\n','',line)
  line = number_processing(line)
  return line

def is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    return False
      
def is_caption(line):
  if line.startswith('<caption>'):
    return True
  else:
    return False


def number_processing(line):
  result = []
  for token in line.split(' '):
    if is_number(token):
      result.append('ᴥnumberᴥ')
      continue
    else:
      result.append(token)
  return ' '.join(result)
      

def get_header_value_info(json_data):
  caption_list = [caption.lower() for caption in json_data['caption']]
  row_header_list = []
  col_header_list = []
  for header_infos in json_data['hv']:
    for header_info in header_infos["row"]:
      row_header_list.extend([row_header.lower() for row_header in header_info['row_header']])
  for header_infos in json_data['hv']:
    for header_info in header_infos["row"]:
      col_header_list.extend([col_header.lower() for col_header in header_info['col_header']])

  return set(caption_list), set(row_header_list), set(col_header_list)

def get_header_value_info_new(json_data, captions):
  
  row_header_list = []
  col_header_list = []
  for header_infos in json_data['hv']:
    for header_info in header_infos["row"]:
      row_header_list.extend([row_header.lower() for row_header in header_info['row_header']])
      col_header_list.extend([col_header.lower() for col_header in header_info['col_header']])

  return set(captions), set(row_header_list), set(col_header_list)

class Node(object):
    def __init__(self, key, data=None):
        self.key=key # character 
        self.data=data # 기존 방식에서는 True/False로 집어넣지만, 여기서는 string or None을 집어넣음.
        self.children = {} # 해당 char에서 다른 캐릭터로 이어지는 children character(key)들과 각 Node(value)

class Trie(object):
    def __init__(self):
        self.head = Node(key=None, data=None)

    def insert_string(self, input_string):
        # Trie에 input_string을 넣어줌
        cur_node = self.head
        for c in input_string:
            if c not in cur_node.children.keys():
                cur_node.children[c] = Node(key=c)
            cur_node = cur_node.children[c]
        cur_node.data=input_string

    def search(self, input_string):
        # input_string이 현재 trie에 있는지 찾아서 TF를 리턴 
        cur_node = self.head
        for c in input_string:
            if c not in cur_node.children.keys():
              continue
                # return False
            else:
                cur_node = cur_node.children[c]
        # if cur_node.data==input_string:
        if cur_node.data == None:
          return False
        if cur_node.data in input_string:
            return cur_node.data
        else:
            return False


    def start_with(self, prefix):
        # prefix로 시작하는 모든 워드를 찾아서 리턴합니다. 
        cur_node = self.head
        words = []
        subtrie = None
        for c in prefix:
            if c in cur_node.children.keys():# 있으므로 값을 하나씩 찾으며 내려감. 
                cur_node = cur_node.children[c]
                subtrie = cur_node
            else:# prefix가 현재 trie에 없으므로, 빈 리스트를 리턴 
                return []
        # 이제 prefix가 존재한다는 것을 알았고, subtrie에 있는 모든 워드를 찾아서 리턴하면 됨. 
        cur_nodes = [subtrie]
        next_nodes = []
        while True:
            for c in cur_nodes:
                if c.data!=None:
                    words+=[c.data]
                next_nodes+=list(c.children.values())
            #print("nn", [n.data for n in next_nodes])
            if len(next_nodes)==0:
                break
            else:
                cur_nodes = next_nodes
                next_nodes = []
        return words


def unit_processing(line, dic):
  result = []

  for token in line.split(' '):
    if dic.search(token):
      result.append('ᴥunitᴥ')
      continue
    else:
      result.append(token)
  return ' '.join(result)  
      


if __name__=='__main__':
  a = 'GCT >8.3mmol/L	12% 42/350	14% 52/371'

  unit_dict = set([re.sub('\n','',unit) for unit in open('./unit.txt','r',encoding='utf8').readlines()])
  t = Trie()
  for unit in unit_dict:
    t.insert_string(unit)
  

  print(t.search('study'))
