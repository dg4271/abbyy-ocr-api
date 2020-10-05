import os
import re
import json


class Semantic:
        
    def __init__(self):
        self.originalCell = ""
        self.poped_populationNumber = ""
        self.populationNumber = 0
        self.textPart = ""
        self.textCleaned = ""
        self.textRepres = ""
        self.attribute = ""
        self.unitPart = ""
        self.unitCleaned = ""
        self.unitRepres = ""
        self.unitPartList = list()
        self.unitCleanedList = list()
        self.unitRepresList = list()
        self.timeLine = ""
        self.headerSign = 0
        # 사전
        self.storedDicHeader = dict()
        self.dicHeader()
        self.storedDicUnit = dict()
        self.dicUnit()
        self.storedDicAttribute = dict()
        self.dicAttribute()
        #추가기능
        self.originalList = list()
        self.taggedEachHeader = list()
        self.fixedText = ""
        self.fixedUnit = list()
        self.fixedType = ""
        self.fixedtimLine = ""
        self.fixedPopulationNumber = list()
    
    def resetParams(self):
        self.originalCell = ""
        self.poped_populationNumber = ""
        self.populationNumber = 0
        self.textPart = ""
        self.textCleaned = ""
        self.textRepres = ""
        self.attribute = ""
        self.unitPart = ""
        self.unitCleaned = ""
        self.unitRepres = ""
        self.unitPartList = list()
        self.unitCleanedList = list()
        self.unitRepresList = list()
        self.unitList = list()
        self.timeLine = ""
        self.headerSign = 0
        #추가기능
        # self.originalList = list()
        self.taggedEachHeader = list()
        self.fixedText = ""
        self.fixedUnit = list()
        self.fixedType = ""
        self.fixedtimLine = ""
        self.fixedPopulationNumber = list()


    ## 사전관리 영역
    def importDicAsDic(self, path):
        try:
            dic = dict()
            with open(path,"r", encoding="utf-8") as f:

                for textLine in f:
                    line = textLine.replace("\n","")

                    # 본인만 있을 경우 본인만 사전 저장
                    if line.find("\t") == -1:
                        dic[line] = line
                        continue

                    # 본인 포함 사전 저장  
                    # 또한 한줄에 탭이 두개이상일 경우 2번째 탭부터는 버린다.           
                    value, keys = line.split("\t")[0], line.split("\t")[1]
                    dic[value] = value
                    for key in keys.split(","):
                        dic[key.strip()] = value

            return dic

        except Exception as e:
            print("[Error] " + path + " loading failed")
            print(e)
            return dict()

    # 지정된 경로의 사전을 가져와 dictionary로 저장
    def dicHeader(self):
        path = os.path.dirname(os.path.abspath(__file__)) + "/dic/" + "dicHeader.txt"
        self.storedDicHeader = self.importDicAsDic(path)
    def dicUnit(self):
        path = os.path.dirname(os.path.abspath(__file__)) + "/dic/" + "dicUnit.txt"
        self.storedDicUnit = self.importDicAsDic(path)
    def dicAttribute(self):
        path = os.path.dirname(os.path.abspath(__file__)) + "/dic/" + "dicAttribute.txt"
        self.storedDicAttribute = self.importDicAsDic(path)

    ## 작업영역
    # 입력값 저장
    def setOriginalCell(self, text):
        self.originalCell =  text
        self.setHeaderSign(0)
        return self.originalCell

    def setHeaderSign(self, digit):
        # 무의미 0 유의미 1
        self.headerSign = digit

    def takePopulationNumber(self):

        cell = self.originalCell

        population_group = re.search(r"(\(? ?n ?= ?(([0-9]+[ ,.]*)+) ?\)?)",cell)

        if (population_group != None ):
            self.poped_populationNumber = cell.replace(population_group.groups()[0], "")
            self.populationNumber = int(re.sub(r"[ ,.]","",population_group.groups()[1]))

        else:
            self.poped_populationNumber = self.originalCell


    def splitHeaderUnit(self):
        cell = self.poped_populationNumber.strip(" .,")
        textPart = cell
        unitPart = ""

        if cell == "":
            return            

        if cell == "%":
            self.unitPart = "%"
            self.unitPartList.append( self.unitPart)
            self.textPart = ""
            return
        
        if re.search(r"95 ?%",cell) != None:
            self.unitPart = ""
            self.unitPartList.append( self.unitPart)
            self.textPart = cell
            return
        
        if cell[-1] == "%":
            self.unitPart = "%"
            self.unitPartList.append(self.unitPart )
            self.textPart = cell[:-1]
            return

        # 띄어쓰기하고 유닛을 표기하는 경우
        # 띄어쓰기하고 오른쪽 마지막 텍스트가 유닛으면 분리한다.
        # 아랫 단위를 유닛에서 제거하였다.
        # weeks	w,week,wk
        # months	m,month
        if len(textPart.split(" ")) > 1:
            if re.match(r"^(([yY](ea)?r?)|([mM](onth)?)|([wW](ee)?k?))s?$", textPart.split(" ")[-1].strip()) == None:
                representativeUnit = self.storedDicUnit.get(textPart.split(" ")[-1], -1)
                if representativeUnit != -1:
                    self.unitPart = representativeUnit
                    self.textPart = ' '.join(textPart.split(" ")[:-1])
                    if self.textPart.strip()[-1] == "," or self.textPart.strip()[-1] == ".":
                        self.textPart = self.textPart.strip()[:-1]  
                    return        
        
        ## 시작 매칭
        # % 로 시작할 경우(% frequency) %를 단위로 나머진 텍스트
        # 그래도 혹시 모르니 괄호나 쉼표가 없으면 return
        if re.match("%", cell) != None:
            self.unitPart = "%"
            self.unitPartList.append( self.unitPart)
            self.textPart = cell[1:]
            cell = cell[1:]
            if re.search("[,(/]", cell) == None:
                return

        # percent of로 시작할 경우 (Percent of Participants) %를 단위로 나머지는 텍스트
        if re.match("[pP]ercent [oO]f", cell) != None:
            self.unitPart = "%"
            self.unitPartList.append( self.unitPart)
            self.textPart = cell[11:]
            return
        # No. of로 시작할 경우(No.of lesions) n을 단위로 나머지는 텍스트
        if re.match("[Nn]umber [oO]f", cell) != None:
            self.unitPart = "n"
            self.unitPartList.append( self.unitPart)
            self.textPart = cell[10:]
            return
        if re.match("[Nn]o[.] [oO]f", cell) != None:
            self.unitPart = "n"
            self.unitPartList.append( self.unitPart)
            self.textPart = cell[7:]
            return
        if re.match("[Nn]o[.]", cell) != None:
            self.unitPart = "n"
            self.unitPartList.append( self.unitPart)
            self.textPart = cell[3:]
            return

        ## 중간 매칭
        # n (%)
        if re.search(r"[nN],? *\(%\)",cell) != None:
            self.unitPart = "n (%)"
            self.unitPartList.append("n")
            self.unitPartList.append("%")
            self.textPart = cell.replace("n (%)","").strip()
            return
        
        # 중간에 %를 포함 한 유형
        if cell.find("%") != -1:
            self.unitPart = "%"
            self.unitPartList.append( self.unitPart)
            self.textPart = cell
            return
        
        # 중간 괄호 찾기 영역
        cell_blank_group = re.search(r"\(([^()]+)\)",textPart)
        if cell_blank_group != None:            
            representativeUnit = self.storedDicUnit.get(cell_blank_group.groups()[0], -1)
            if representativeUnit != -1:
                self.unitPart = representativeUnit
                self.textPart = textPart
                return                    

        if len(textPart.split(" ")) > 1:
            representativeUnit = self.storedDicUnit.get(textPart.split(" ")[-1], -1)
            if representativeUnit != -1:
                self.unitPart = representativeUnit
                self.textPart = ' '.join(textPart.split(" ")[:-1]) 
                return        
        
        ## 분리 영역
        # 1차 분리기준 괄호의 유무
        if cell.find(")") != -1:
            # 2차 분리 기준 문자(단위)로 끝나지 않고 문자(보충설명)문자로 끝나는 경우제외 
            if ( cell.find(")") >= (len(cell) - 1) ):
                textPart = cell[:cell.find("(")]
                unitPart = cell[cell.find("("):cell.find(")")+1]                

            # 문자부분에 ,가 들어갈경우 단위가 두 번 들어갈 확률이 매우 높음
            if ( textPart.find(",") != -1):
                textPart = cell[:cell.find(",")]
                unitPart = cell[cell.find(","):cell.find(")")+1]
                    
        # 1차 분리기준 콤마의 유무
        elif cell.find(",") != -1:
            textPart = cell[:cell.find(",")]
            unitPart = cell[(cell.find(",")+1):]
            
        ## 저장 영역
        self.textPart = textPart
        self.unitPart = unitPart
        self.unitPartList.append( self.unitPart)

    def checkTimeLine(self):
        # 타임라인 표현식
        timeLine_match_exp = r"^([1-9]* ?([mM]in[ute]?s?|[hH]ours?|[mM]onth[s]?|[yY]ear[sS]?|[yY]rs?|[wW]eeks?) ?[1-9]*)$"
        timeLine_search_exp = r"([0-9]* ?[<>]* ?([aA]t)? ?[0-9]+ ?(([mM]in[ute]?s?)|([hH]ours?)|([mM]onth[s]?)|([yY]ear[sS]?)|([Yy]rs?)|([wW]eeks?)))"
        
        timeLine_match = re.match(timeLine_match_exp, self.textPart)
        timeLine_search = re.search(timeLine_search_exp, self.textPart)   

        if timeLine_match != None:
            timeLine_match_grouped = timeLine_match.groups()
            self.timeLine = timeLine_match_grouped[0].strip()
            self.textPart = self.textPart.replace( timeLine_match_grouped[0], "" )

        if timeLine_search != None:
            timeLine_search_grouped = timeLine_search.groups()
            self.timeLine = timeLine_search_grouped[0].strip()
            self.textPart = self.textPart.replace( timeLine_search_grouped[0], "" )
        
        return

    def cleanHeader(self):
        # 전처리 영역
        # 양옆 공백제거
        textPart = self.textPart.strip("., ")

        # 캡션 제거

        # 텍스트로 흘러들어간 단위 복귀
        if self.textPart == "N" or self.textPart == "n":
            self.unitRepresList.append(textPart)
            self.textPart = ""
            textPart = ""
        
        # 텍스트가 없을 경우 조기종료
        if textPart == "":
            self.textCleaned = textPart
            return

        # 저장 영역
        self.textCleaned = textPart.strip("., ")
        return self.textCleaned
    
    def getRepresentativetHeader(self):
        # textRepres의 기본값을 ""로
        self.textRepres = ""

        # 텍스트가 없을 경우 대표값이 없으므로 조기 종료
        if self.textCleaned == "":
            return self.textRepres
        
        # 사전에서 대표값 찾아서 종료
        representative = self.storedDicHeader.get(self.textCleaned.lower(), -1)
        if representative != -1:
            self.textRepres = representative
            # 대표값이 있음을 명시
            self.setHeaderSign(1)
            return self.textRepres
            
        representative = self.storedDicAttribute.get(self.textCleaned.lower(), -1)
        if representative != -1:
            self.textRepres = self.textCleaned
            # 대표값이 있음을 명시
            self.setHeaderSign(1)
            return self.textRepres
        

        return self.textRepres


    def cleanUnit(self):
        # 전처리 영역
        # 양옆 공백제거
        unitPart = self.unitPart.strip()
        unitPocket = list()

        # 단위 영역이 없을 경우 조기 종료
        if unitPart == "":
            self.unitCleaned = unitPart
            return self.unitCleaned

        # n (%) 사용자 정의
        if unitPart == "n (%)":
            self.unitCleaned = unitPart
            self.unitRepresList.extend(["n","%"])
            return self.unitCleaned

        # degree 단위 먼저 확인
        if unitPart.find("°C") != -1:
            self.unitCleaned = "°C"
            unitPocket.append(unitPart)   
            self.unitRepresList.extend(unitPocket)
            return self.unitCleaned

        # 제일먼저 양끝 괄호()부터 제거
        if unitPart.find("(") == 0:
            if unitPart.find(")") == len(unitPart)-1:
                unitPart = unitPart[1:-1]

        # 제일 앞이 "," 일경우 제거
        if unitPart[0] == ",":
            unitPart = unitPart[1:].strip()
        # ,로 두개의 단위가 있을 시
        if unitPart.find(",") != -1:
            # "," 자체일 경우 공백으로둔다.
            if unitPart == ",":
                unitPart = ""
            # "," 자체가 아니면, 가장 앞에 있는 유닛 추출, 그리고 양옆 공백제거   
            else:    
                unitPart = unitPart.split(",")[0].strip()
                # 뒤에 놈들도 살려내
                unitPocket.extend( unitPart.split(","))

        # %를 포함한 경우
        # 정보가  중요할 수 있음 (%, 95% CI, % energy)
        if unitPart.find("%") != -1:
            self.unitCleaned = unitPart
        
        # / 기호가 들어간 경우
        if unitPart.find("/") != -1:
            # 바로 공백이 나타날 경우 / 기준 바로 왼쪽과 오른쪽을 붙인다.
            unitPart = unitPart.replace("/ ","/").replace(" /","/")

            # 양옆에 문자나 숫자가 이어지는 부분까지 자른다.
            if re.search(r"[a-zA-Z0-9]+\%[a-zA-Z0-9]+", unitPart) !=None:
                unitPart = re.search(r"[a-zA-Z0-9]+\%[a-zA-Z0-9]+", unitPart).group()
            
        # 맨 앞에 있는 특수문자 제거, %는 살려둔다.
        if re.search(r"[0-9a-zA-Z%]",unitPart ) != None:
            unitPart = unitPart[re.search(r"[0-9a-zA-Z%]",unitPart ).span()[0] : ]

        # OCR문제 ex) m2 
        unitPart = unitPart.replace("m2 ","m² ").replace("m3 ","m³ ").replace("/24h","/24 h")

        unitPocket.append(unitPart)        

        # 저장 영역
        self.unitCleaned = unitPart
        self.unitRepresList.extend(unitPocket)
        return self.unitCleaned

    def getRepresentativeUnit(self):
        self.unitRepres = ""
        unitPocket = list()

        # 미리 저장된 유닛들 확인한번만 더하자
        for unit in self.unitRepresList:
            representative = self.storedDicUnit.get(unit, -1)
            if representative != -1:
                unitPocket.append( representative )
        self.unitRepresList = unitPocket

        # 단위 영역이 없을 경우 조기 종료
        if self.unitCleaned == "":
            self.unitRepres = self.unitCleaned
            return self.unitCleaned

        # 사전에서 대표값 찾아서 종료
        representative = self.storedDicUnit.get(self.unitCleaned, -1)
        if representative != -1:
            self.unitRepres = representative

            # 단위가 있으면 헤더에 유의미
            self.headerSign = 1
            return self.unitRepres
        
        if self.unitRepres == "":
            if self.textRepres == "":
                self.textCleaned = self.textCleaned +", "+ self.unitCleaned
            else:
                self.textRepres = self.textRepres +", "+ self.unitCleaned

        return self.unitRepres
    
    def getHeaderValueType(self):
        self.attribute = "unknown"

        # group이라고 나오면 그룹이다!
        group_exp = r"[gG]roup|[aA]lternative|[cC]ontrol[s]?|[eE]xperiment|[nN]ormal|[tT]reatment"
        if re.search( group_exp, self.textCleaned) != None:
            self.attribute = "group"

        # 사전에서 속성이 있으면 속성이라 하자
        headerType = self.storedDicAttribute.get(self.textCleaned.lower(), -1)
        if headerType != -1:
            self.attribute = "attribute"
        
        # 20200917 CJ요청 - 단위가 있으면 attribute로 해주세요.
        # 20200929 컬럼 로우 스위칭 문제 때문에 제거.
        # if  self.unitRepres != "":
        #     self.attribute = "attribute"

    def getResultDict(self):
        output = dict()
        output["originalCell"] = self.originalCell
        output["textPart"] = self.textPart ### 필요없음
        output["textCleaned"] = self.textCleaned
        output["textRepres"] = self.textRepres
        output["unitPart"] = self.unitPart ### 필요없음
        output["unitCleaned"] = self.unitCleaned
        output["unitRepres"] = self.unitRepres
        output["unitRepresList"] = self.unitRepresList
        output["timeLine"] = self.timeLine
        output["type"] = self.attribute
        output["populationNumber"] = self.populationNumber
        return output
    
    def tagged_header(self, text):
        self.resetParams()
        self.setOriginalCell(text)
        self.takePopulationNumber()
        self.splitHeaderUnit()
        self.checkTimeLine()
        self.cleanHeader()
        self.cleanUnit()
        self.getRepresentativetHeader()
        self.getRepresentativeUnit()
        self.getHeaderValueType()
        return self.getResultDict()

    '''
    추가 기능 구현부
    '''
    def setOriginalList(self, header_list):
        self.originalList = header_list

    def tagEachHeader(self):
        output = list()
        for text in self.originalList:
            output.append( self.tagged_header(text))

        self.taggedEachHeader = output
        return output

    def fixResults(self):
        taggedHeaders = self.taggedEachHeader
        textQue = ""
        typeStack = list()

        for taggedHeader in taggedHeaders:
            # text
            if isTableCaption( taggedHeader["originalCell"] ):
                textQue = ""
            elif taggedHeader["textRepres"] !="":
                textQue = taggedHeader["textRepres"]
            elif taggedHeader["textCleaned"] != "":
                textQue = taggedHeader["textCleaned"]
            elif taggedHeader["textPart"] != "":
                textQue = taggedHeader["textPart"]
            elif taggedHeader["unitRepresList"] != []:
                textQue = ""
            else :
                textQue = taggedHeader["originalCell"]

            # text and timeline
            if taggedHeader["timeLine"] == "":
                self.fixedText = self.fixedText + " " + textQue
            else:
                self.fixedtimLine = taggedHeader["timeLine"]
                self.fixedText = self.fixedText + " " + textQue
            self.fixedText = self.fixedText.strip(" .,").replace("  "," ")
            
            # type 1단계 타입 모으기
            typeStack.append(taggedHeader["type"])
            
            # unit
            if taggedHeader["unitRepresList"] != []:
                # 단위 모으기
                for unitPiece in taggedHeader["unitRepresList"]:
                    self.fixedUnit.append(unitPiece)            

            # populationNumber
            if taggedHeader["populationNumber"] != 0:
                self.fixedPopulationNumber = taggedHeader["populationNumber"]
        
        # type 2단계 타입추출된 상황에 따라 타입 지정하기
        if len(typeStack) != 0:
            if typeStack[-1] == "attribute":
                self.fixedType = "attribute"
            elif typeStack[-1] == "group":
                self.fixedType = "group"
            else:
                self.fixedType = "unknown"
        else:
            self.fixedType = "unknown"

    def getResultDict2(self):
        output = dict()
        output["text"] = self.fixedText
        output["unit"] = self.fixedUnit
        output["type"] = self.fixedType
        output["timeLine"] = self.fixedtimLine
        output["populationNumber"] = self.fixedPopulationNumber
        output["originalList"] = self.originalList
        
        logs = dict()
        logs["results"] = self.taggedEachHeader
        output["log"] = logs
        return output

    def tagged_list_header(self, header_list):
    
        if header_list == []:
            return dict()

        self.resetParams()
        self.setOriginalList( header_list )
        self.tagEachHeader()
        self.fixResults()

        return self.getResultDict2()


def isTableCaption( text ):
    import re
    if re.match(r"[tT]able|[dD]stribution", text) != None:
        return True
    if len(text) > 100:
        return True
    return False

if __name__ == "__main__":

    '''
    이전 버전 예시
    '''
    # print("-"*50)
    # st_module = Semantic()
    # output = st_module.tagged_header("Blood glucose( mg/dL), n = 20")
    # print(json.dumps(output, indent=3))
    # print("-"*50)


    '''
    - 추가기능 테스트
    - 인풋: row_header 리스트 또는 col_header 리스트
    - 아웃풋: 태깅 된 정보를 반환
    - 예시
        - 인풋 :
            [ "Yes BreakFast (n = 576)", "Without Supplement (n = 495)", "3 month", "n (%)" ]
        - 아웃풋 :
            {
                text : "Yes BreakFast Without Supplement"
                unit : [ "%", "n"]
                type : "unknown"
                timeLine : "3 month"
                populationNumber : 495
                log : {"separately": [{ "originalcell": ...}, ..., { ...}] }
            }

    '''
    # print("-"*50)
    # st_module = Semantic()
    # output = st_module.tagged_list_header([ "Yes BreakFast (n = 576)", "Without Supplement (n = 495)", "3 month", "n (%)" ])
    # print(json.dumps(output, indent=3))
    # print("-"*50)



    '''
    개발하면서 테스트 해보기 위한 아랫 영역
    '''
    st_module = Semantic()
    # print("-"*50)
    # output = st_module.tagged_header("Blood glucose (n=10) (n)%")
    # print(json.dumps(output, indent=3))
    # print("-"*50)
    print("-"*50)
    output = st_module.tagged_list_header([
                         "Model 1",
                                "OR (95% CI)",
                                ". . . . . P",
                                "J • ■ • : 1.04(0.99-1.09)"
                    ])
    print(json.dumps(output, indent=3))
    print("-"*50)
