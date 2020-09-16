import re
import json

'''
시멘틱 태깅 모듈 테스트
'''
import table_semantic_tagging.semantic_tagging as tagger
# print("lets start")
st_module = tagger.Semantic()
output1 = st_module.tagged_header("Blood glucose( mg/dL), n = 20 ")
output2 = st_module.tagged_header("bmi, N (%)")
output3 = st_module.tagged_header("your Groups")

# print("1","-"*50)
# print(json.dumps(output1, indent=3))
# print("2","-"*50)
# print(json.dumps(output2, indent=3))
# print("3","-"*50)
# print(json.dumps(output3, indent=3))
# print("end","-"*50)

'''
부수적인 테스트
'''

# print(re.search(r"(\( ?n ?= ?([0-9]+) ?\))","age ( n = 301 )").groups())
# print(len(re.search(r"(\( ?n ?= ?([0-9]+) ?\))","age ( n = 301 )").groups()))
# print(re.search(r"(\(? ?n ?= ?([0-9]+) ?\)?)","Cases (study volunteers) n = 48").groups())

# tmp = "age ( n = 1)"
# print(re.search(r"(\( ?n ?= ?([0-9]+) ?\))",tmp).groups())
# tmp2 , tmp3 = re.search(r"(\( ?n ?= ?([0-9]+) ?\))",tmp).groups()
# print(tmp2)
# print(tmp.replace(tmp2,""))

# print("-"*100)
# print(re.search(r"(\(? ?n ?= ?([0-9]+) ?\)?)", "group (n = 10)").groups())
# print(re.search(r"(\(? ?n ?= ?(([0-9]+[ ,.]?)+) ?\)?)", "group (n = 10 000 00)").groups())
# print(int( re.sub(r"[. ]","","122. 333")))

# print(re.search(r" *([pP]+[- _.]?([vV]alue)?) *", "p value").groups())
# print(re.search(r" *([pP]+[- _.]?([vV]alue)?) *", "p value") != None)
# print(re.match(r"([pP][- _.][vV]alue)", ""))
# print("daAA".lower())
# print("95d% ci".find("95%"))
print("-"*50)
output = st_module.tagged_list_header([
                    
                ])
# 출력
print("-"*50)
print(json.dumps(output, indent=3))
print("-"*50)

def isTimeLine( text ):
    # 어떤 처치를 얼마만큼 했다?

    return True
print( isTimeLine( " gg"))
