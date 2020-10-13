import re

from table_semantic_tagging.semantic_tagging import Semantic


class ValueRegularizer():
    def __init__(self):
        self.st_module = Semantic()
        
        p_value_header = "[pP][12]?( group| interaction|[ \-]?[vV]a[!l]ue[s]?( for( intervention)?| \(HW\))?|( for |-)(linear )?trend( [a-z ]+|1)?| \((hot voxel|chi square)\))? ?[:*1-8a-hty]?( -)?"
        p_value_header_not_startwith_p = "[Mm]ixed[ \-]model( ANOVA)?|[AT][0-9]? vs\.? [AT][0-9]?"
        self.p_value_header= "(^{}| {})$".format(p_value_header, p_value_header)
        
        self.pre_symbol = "(([ \\\\«~#\^|•:■/*;,'’!_di-km)][ \\\\«~#\^|•■</*:;,'’!_di-km)]*[hJX \^]*|GFR|(Md)?-?[ •:;'m]+|1-[ *:]+)*)"
        self.post_symbol = "(([•■;\^\*%#&$§_\-<‘’”“\"',. ()|\\\\]|[+A-CGPTXZa-flmnstwxy])*|[(][a-zR. \-]+[)])"

        self.p_value_tag = "(Interaction)? ?[pP]( value)? ?[—=<>]"
        _n_type = "([<>+\-±—§~]|min|max|up to pH|SD|%s|([nr]|rho) ?[ =<>] ?[—\-]?|T:|-? ?\$|-50[GT]{,2} =)?" % (self.p_value_tag)
        _number = "0[,\-][0-9]+|[1-9]-[0-9]{2,}|[0-9]+-0[0-9]+|[0-9 ]*[0-9]-[0-9]|[0-9 ]+[0-9]+-[0-9]{2}|\.?[0-9]"
        _power = "[0-9.'’\^][0-9.'’\^\-]* ?([xX*] ?10|[Ee])-?[0-9]+"
        _num_w_error = "([0-9lo]|Q-|i[.0-9]|(\.|- ?)[0-9])[ 0-9lOQSf.,'’:\^]*[0-9lOQSf.'’:\^]+"
        _numeric = " ?(%s|%s|%s)[*]*" %(_power, _num_w_error, _number)

        # single unit과 left/right unit, 그 외로 나눠서 만들면 좋을 듯
        _unit1 = "°C|%[CEFP]?|[mpu]?I? ?U(/[dmL]{,2})?.*|c?m|meters|ms2|m2/kg|kg(/m2?| DM/ha)?|lb|MJ/kg DM|mm ?Hg|mM|[μm]U/mL"
        _size_unit = "mmol/mol|([nmp]?c?g|MCU)/[dmlL]{,2}|[mp]?g%?|[mnp]m[°o]l/[Ll]|mmol-1|mL/min"
        _energy_unit = "[Kk]cal/(mL|day)|k[jJ](/cal)?"
        _unit2 = "[(]IgG[12][)]|RAE|HD( and PD)?|PD|py|(g|min|servings)/(week|day).*|days?|[yY]ears|-?months?"
        _unit3 = "sibling/related|unrelated|light|moderate|bar|min|hh:mm|h( oral)?"
        _sex = "(% )?\(?(wo)?men\)?|(fe)?male|[(][MF][)]"
        _etc_unit = "% CM|m?g/dia( TTS)?|mg i\.m\.|/?semanas?|kg( peso)?|% f (fuerza|area|volumen) [a-z0-9 ]+|with( and|out body mass reduction)"
        self.unit = "{}|{}|{}|{}|{}|{}|{}".format(_unit1, _unit2, _unit3, _size_unit, _energy_unit, _sex, _etc_unit)

        value_pattern0 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(0, _n_type, _numeric, self.unit)
        value_pattern1 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(1, _n_type, _numeric, self.unit)
        value_pattern2 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(2, _n_type, _numeric, self.unit)
        value_pattern3 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(3, _n_type, _numeric, self.unit)
        
        self.p1 = "[(]?(%s)[)]?" %(value_pattern0) # N | (N)
        self.p2 = "%s ?(?P<separator>to|[ ,±+—\-/;:]| [.6] ) ?%s" %(value_pattern0, value_pattern1) # N N
        self.p3 = "[C{(\[] ?%s ?[)\]]" %(self.p2)  # (N N)
        self.p4 = "%s ?_?[C({\[] ?%s ?[_)\]]{,2}" %(value_pattern0, value_pattern1) # N (N)
        self.p5 = "%s[; ] ?%s" %(self.p2, value_pattern2) # N N N
        self.p6 = "%s[ ,/] ?%s" %(value_pattern2, self.p2) # N N N
        self.p7 = "%s ?%s" %(value_pattern2, self.p3) # N (N N)
        self.p8 = "%s ?[C({\[]%s[)\]]" %(self.p2, value_pattern2) # N N (N)
        self.p9 = "%s ?_?[C({\[] ?%s ?[_)\]] ?[C({\[] ?%s ?[_)\]]" %(value_pattern0, value_pattern1, value_pattern2) # N (N) (N)
        self.p10 = "%s[ ,;] ?%s[ ,;] ?%s" %(value_pattern2, self.p2, value_pattern3) # N N N N
        self.p11 = "%s ?(?P<separator2>[±:/])%s ?%s" %(value_pattern2, value_pattern3, self.p3) # N N (N N)
        self.p12 = "%s[ ,;] ?%s" %(self.p7, value_pattern3)  # N (N N) N
        # Men (70.5 ±1.9 years) Women (78.3 ±1.2 years)
        # F: 7.4-9.9 M: 8.4-10.8
        #self.p13 = "(([FM]|(M|Wom)en):? ?%s ?){2}" %(self.p2) # 수정 필요

    def _regularize_numeric(self, n):
        if ", " in n:
            return None

        n = n.replace(' ', '')
        n = re.sub("[''’:\^]", '.', n)
        n = re.sub("([f.,*]+$)", '', n)
        if re.search("[Xx*Ee]", n):
            power_n = re.split("([xX*] ?10|[Ee])", n)
            if len(power_n) == 1 or not power_n[2]:
                return None
            n = float(power_n[0].replace('-', '.')) * (10**int(power_n[2]))
        else:
            n = n.replace('S', '5')
            n = re.sub("[QOo]", '0', n)
            n = re.sub("[|lIi]", '1', n)

            if re.search("^\d{2} ?[—\-] ?\d{2,}", n):
                n1, n2 = re.split(" ?[—\-] ?", n)
                if int(n1) < int(n2):
                    return None

            n = n.replace('-', '.')
            comma_n = n.split(',')
            # 이거 왜 넣었던 걸까?
            #if len(comma_n) > 1 and not re.search("^\d{3}[^0-9]*", comma_n[1]):
            #    return None
            if comma_n[0] == '0' or (len(comma_n) > 1 and len(comma_n[1].split('.')[0]) !=3):
                n = n.replace(',', '.')
            else:
                n = n.replace(',', '')
            n = n.replace("..", '.')
            if re.search("^0\d+$", n):
                n = "0.{}".format(n[1:])
            try:
                n = float(n)
            except ValueError:
                return None
        return n

    def _add_type(self, n_type, value_dic):
        type_dic = {
            "min": "min",
            "max": "max",
            "SD": "SD",
            "<": "less",
            "~": "less or equal",
            ">": "more",
            "±": "SD",
            "§": "SD"
        }
        unit_dic = {
            "$": "$",
            "T:" : "T"
        }

        if n_type in unit_dic:
            value_dic["unit"] = unit_dic[n_type]
        elif n_type == "up to pH":
            value_dic["type"] = "less or equal"
            value_dic["unit"] = "pH"
        elif n_type.startswith('n'):
            value_dic["unit"] = "n"
        elif n_type.startswith('r'):
            value_dic["unit"] = "rho_value"
        elif re.search("^{}$".format(self.p_value_tag), n_type):
            value_dic["unit"] = "p_value"

        if re.search("[<>]", n_type):
            n_type = re.search("[<>]", n_type)[0]
        if n_type in type_dic:
            value_dic["type"] = type_dic[n_type]
        elif value_dic["value"] != None and value_dic["unit"] != "p_value" and re.search("^[—\-]$", n_type):
            value_dic["value"] *= -1

        return value_dic

    def regularize_value(self, t, number_of_values=None):
        original_t = t
        t = re.sub("(: )+", "", t)
        t = t.replace("<br>", ' ')
        t = re.sub("^(4-|-3) (\d.+)$", "\g<2>", t) # 하드코딩
        t = re.sub(" >4", "", t) # 하드코딩
        
        for i in range(1, 13):
            pattern = "^%s%s%s$" %(self.pre_symbol, eval("self.p{}".format(i)), self.post_symbol)
            groups = re.search(pattern, t)
            comma_splited = t.split(',')
            result = None
            
            if not groups:
                continue
            elif i == 1:
                comma_splited = t.split(',')
                if ' 6 ' in t or (t.find('-') > 0 and re.search("[,(][^\-]", t)) \
                    or ('(' in t and ", " in t) \
                    or (number_of_values and number_of_values > 1):
                    continue

            number_of_numerics = sum(1 for key in groups.groupdict().keys() if "numeric" in key)
            if number_of_values and number_of_numerics != number_of_values:
                continue

            result = []
            for j in range(number_of_numerics):
                n = self._regularize_numeric(groups.group("numeric{}".format(j)))
                unit = groups.group("unit{}".format(j))
                unit = unit.replace("mm°l/L", "mmol/L") if unit else None
                value_dic = {
                    "originalCell": original_t,
                    "value": n,
                    "unit": unit,
                    "type": "default"
                }
                value_dic = self._add_type(groups.group("type{}".format(j)), value_dic)
                result.append(value_dic)
            
            if any(value_dic["value"] == None for value_dic in result):
                continue

            sep = groups.groupdict().get("separator", "")
            if sep == '±' and '-' in groups.groupdict().get("numeric2", ""):
                continue

            if re.search("[.±6]", sep):
                result[0]["type"] = "mean"
                result[1]["type"] = "SD"
            elif re.search("(to|[—\-])", sep) or (re.search("[C{(\[].+,.+[)\]]", t)) \
                or (result[0].get("type") == "min" and result[1].get("type") == "max"): # Integration to range
                result[0]["type"] = "range"
                result[0]["value"] = tuple(r["value"] for r in result[:2])
                if result[1]["unit"]:
                    result[0]["unit"] = result[1]["unit"]
                result.pop(1)
            elif len(result) == 2 and len([r for r in result if r["unit"] == '%']) == 1:
                for i in range(2):
                    if result[i]["unit"] != '%' and int(result[i]["value"]) == result[i]["value"]:
                        result[i]["unit"] = "n"
            elif len(result) == 3 and sep == '/' and result[2]["unit"] == '%': # N1/N2 N3%인 경우, 첫 번째 N은 대상자수, 두 번째 N은 전체 대상자수
                if result[0]["value"] > result[1]["value"]:
                    result[0], result[1] = result[1], result[0]
                result[0]["unit"] = "n"
                result[1]["unit"] = "n"
                result[1]["type"] = "total"

            if len(result) == 0:
                continue
            elif i == 1 and number_of_values == None and result[0]["unit"] == "%" and result[0]["value"] > 100:
                continue
            elif len(result) == 3 and t.count('±') == 2:
                continue
            elif i == 11:
                sep = groups.groupdict().get("separator2", "")
                if sep == '±':
                    next_ = 1 if result[0]["type"] == "range" else 2
                    result[next_]["type"] = "mean"
                    result[next_+1]["type"] = "SD"
                sep_idx = 2 if len(result) == 4 else 1
                result = result[sep_idx:] + result[:sep_idx]
            elif i in set([6, 7, 10, 12]):
                if result[0]["type"] == "range":
                    result = [result[1]] + [result[0]] + result[2:]
                else:
                    result = [result[2]] + result[:2] + result[3:]

            return result

        return []
    
    def update_p_value(self, row_header, col_header, values, value_is_ns):
        is_p_value = False
        if (col_header and any(re.search(self.p_value_header, c) for c in col_header)) \
            or (row_header and re.search(self.p_value_header, row_header[-1])) \
            or (len(row_header) > 1 and re.search(self.p_value_header, row_header[0])):
            is_p_value = True
        
        # p_value 업데이트
        significant_threshold = 0.05
        if is_p_value and len(values) == 1 and values[0]["type"] != "range" and values[0]["value"] <= 1:
            values[0]["unit"] = "p_value"
            values[0]["significant"] = values[0]["value"] <= significant_threshold
        elif any(v["unit"] == "p_value" for v in values):
            for i in range(len(values)):
                if values[i]["unit"] == "p_value":
                    values[i]["significant"] = values[i]["value"] <= significant_threshold
        elif value_is_ns:
            values = [{
                "value": None,
                "unit": "p_value",
                "significant": False
            }]

        return {
            "row_header": row_header,
            "col_header": col_header,
            "value": values
        }
    
    def strip_header(self, header_list, idx, pattern):
        striped_header = re.sub(pattern, "", header_list[idx])

        if not striped_header:
            header_list.pop(idx)
        else:
            header_list[idx] = striped_header
        return header_list
    
    def regularize_header(self, header_list):
        replace_unit_in_header = {
            "\(mmo (l\"1|T1)\)": "(mmol-1)",
            #"\(pU/mL\)": "(μU/mL)"
        }
        for i in range(len(header_list)):
            for pattern, replace in replace_unit_in_header.items():
                header_list[i] = re.sub(pattern, replace, header_list[i])

        return header_list
    
    def regularize_value_with_header(self, header_and_value):
        row_header = self.regularize_header(header_and_value["row_header"])
        col_header = self.regularize_header(header_and_value["col_header"])
        number_of_values = None
        
        # 단위 추출
        units = []
        n_pattern = "(^([nN]|(Number|No.)( of .+)?|Frequency)|, n)$"
        n_percent_pattern = "(^N(o\.)? \(|(Frequencies)?[ \(][Nn],? ?\(?)%( men)?\)"
        sex_pattern = "[mfMF]|([Ff]e)?[Mm]ale"
        percent_pattern = "[\[(]?%[\])]?$"
        unit_pattern = "([\[(]|, )(?P<unit>%s)[\])]?[ab]?$" %(self.unit)
        row_unit = re.search(unit_pattern, row_header[-1]) if row_header else None
        col_unit = re.search(unit_pattern, col_header[-1]) if col_header else None
        unit_in_column = True
        
        n_percent_col_idx = -1
        for idx, ch in enumerate(col_header):
            if re.search(n_percent_pattern, ch):
                n_percent_col_idx = idx
                break
        percent_col_idx = -1
        for idx, ch in enumerate(col_header):
            if re.search(percent_pattern, ch) and "95%" not in ch:
                percent_col_idx = idx
                break
        
        if n_percent_col_idx != -1:
            #col_header = self.strip_header(col_header, n_percent_col_idx, n_percent_pattern)
            units.append("n")
            units.append("%")
            number_of_values = 2
        elif col_header and re.search(n_pattern, col_header[-1]):
            #col_header = self.strip_header(col_header, -1, n_pattern)
            units.append("n")
        elif row_header and re.search(n_percent_pattern, row_header[-1]):
            #row_header = self.strip_header(row_header, -1, n_percent_pattern)
            units.append("n")
            units.append("%")
            number_of_values = 2
            unit_in_column = False
        elif percent_col_idx != -1 and col_header[-1] != "SE":
            col_header = self.strip_header(col_header, percent_col_idx, percent_pattern)
            units.append('%')
        elif row_unit:
            row_header = self.strip_header(row_header, -1, unit_pattern)
            units.append(row_unit.group("unit"))
            unit_in_column = False
        elif col_unit:
            col_header = self.strip_header(col_header, -1, unit_pattern)
            units.append(col_unit.group("unit"))
        # male, female 구분은 여기서 할 수 있군.
        elif row_header and re.search("\((%s)/(%s)\)[Z]?$" %(sex_pattern, sex_pattern), row_header[-1]):
            units.append("n")
            units.append("n")
            number_of_values = 2
            unit_in_column = False
        
        # 타입 추출
        types = []
        single_type_pattern = "(Mean|SE)$"
        mean_SD_pattern = "[Mm]ean ?[±\(] ?SD\)?"
        if col_header and re.search(mean_SD_pattern, col_header[-1]):
            col_header = self.strip_header(col_header, -1, mean_SD_pattern)
            types.append("mean")
            types.append("SD")
            number_of_values = 2
        elif col_header and re.search(single_type_pattern, col_header[-1]):
            col_header = self.strip_header(col_header, -1, mean_SD_pattern)
            unit = re.search(single_type_pattern, col_header[-1]).group(0)
            if not unit.isupper():
                unit = unit.lower()
            types.append(unit)
            number_of_values = 1
        
        # value 추출
        values = self.regularize_value(header_and_value["value"], number_of_values)
        
        # 타입 업데이트
        if len(types) == len(values):
            for i in range(len(types)):
                values[i]["type"] = types[i]
        
        # 헤더 정보 가져오기 (이욱 주임 모듈 사용)
        row_header_info = self.st_module.tagged_list_header(header_and_value["row_header"])
        col_header_info = self.st_module.tagged_list_header(header_and_value["col_header"])
        
        # 헤더 정보에 추출된 유닛이 있는 경우
        # 1. type이 attribute인 곳의 유닛을 사용
        # 2. type이 group인 곳이 아닌 곳의 유닛 사용
        # 3. 둘 다 unknown 또는 둘다 group이면 row에 있는 유닛 사용
        if col_header_info and col_header_info.get("unit") and (
            (col_header_info.get("type") == "attribute" and row_header_info.get("type") != "attribute") 
            or (col_header_info.get("type") == "unknown" and row_header_info.get("type") == "group")):
            units = col_header_info["unit"]
        elif row_header_info and row_header_info.get("unit") and (row_header_info.get("type") == "attribute" 
            or (row_header_info.get("type") == "unknown" and col_header_info.get("type") != "attribute")
            or (row_header_info.get("type") == "group" and col_header_info.get("type") != "group")):
            units = row_header_info["unit"]

        # 단위 업데이트
        if units and len(units) == len(values) and all(v["unit"] == None for v in values):
            for i in range(len(units)):
                if units[i] == "n" and int(values[i]["value"]) != values[i]["value"]:
                    continue
                else:
                    values[i]["unit"] = units[i]
        elif len(units) == 1 and values and values[0]["unit"] == None:
            unit = units[0]
            # 헤더에 %만 있는데, 값이 두 개고, 둘 다 unit이 없고, 앞의 값이 소수가 아니고, 뒤에 값이 0~100이면, 앞은 n, 뒤는 %로.
            if unit == '%' and len(values) == 2 and all(v["unit"] is None for v in values) \
                and all(v.get("type") != "range" for v in values) \
                and int(values[0]["value"]) == values[0]["value"] and 1 <= values[1]["value"] <= 100:
                values[0]["unit"] = 'n'
                values[1]["unit"] = '%'
            elif unit == "hh:mm":
                for i in range(len(values)):
                    values[i]["value"] = str(values[i]["value"]).replace('.', ':')
                    values[i]["unit"] = units[0]
            else:
                for v_i in range(len(values)):
                    if values[v_i]["unit"]:
                        break
                    values[v_i]["unit"] = unit
        elif units and len(units) <= len(values):
            i = 0
            for v_i in range(len(values)):
                if values[v_i]["unit"]:
                    break
                values[v_i]["unit"] = units[i]
                if i < len(units) - 1:
                    i += 1
            
        
        # P value 업데이트
        value_is_ns = header_and_value["value"].lower() == "ns"
        header_and_value = self.update_p_value(row_header, col_header, values, value_is_ns)
        header_and_value["row_header"] = row_header_info
        header_and_value["col_header"] = col_header_info
        
        # TODO: Population Number 정보를 모든 value에 넣어야 하나? 아니면 unit이 n인 경우에만 넣으면 되나? -> 동균 주임
        
        return header_and_value


if __name__ == "__main__":
    """
    - input: value 문자열 // 희원 주임이 주는 데이터에 따라 input 변경될 수 있음
    - output: 정규화된 value 딕셔너리
    
    <딕셔너리 key-value 안내>
    ["originalCell"]: 원본 텍스트
    ["value"]       : 텍스트로부터 추출된 숫자값
    
    ["type"] *더 추가될 예정*
    "default"       : 아무 타입도 아닌 경우, 기본값으로 주어짐.
    "range"         : "value"에 tuple(최솟값, 최댓값)으로 저장되어 있음.
    "mean           : 평균
    "SD"            : 표준편차
    "less"          : 작음
    "less or equal" : 작거나 같음
    "more"          : 큼
    
    ["unit"] *대표적인 것만 추가함*
    "n"             : 사람 수를 나타냄.
    "%"             : 전체에서의 대상자 비율을 나타냄
    "p_value"       : p value 값을 나타냄.
    
    ["significant"] : unit이 "p_value"인 경우에 한해서 존재하며, 0.05 이하인 경우 True, 그 외 False
    
    """
    # Value 정보만 주는 경우
    vr = ValueRegularizer()
    print(vr.regularize_value("1.21 ± 3.19"))
    """
    출력 결과
    [
      {
        'value': 1.21,
        'unit': None,
        'originalCell': '1.21 ± 3.19',
        'type': 'mean'
      },
      {
        'value': 3.19,
        'unit': None,
        'originalCell': '1.21 ± 3.19',
        'type': 'SD'
      }
    ]
    """
    
    # 헤더 정보와 같이 주는 경우
    test = {
        "row_header": ['Control N (%)'],
        "col_header": ['Intervention (n = 29)'],
        "value": "192(33.8)"
    }
    print(vr.regularize_value_with_header(test))
    """
    출력결과
    {
        'row_header': {
            'text': 'control group',
            'unit': [],
            'type': 'group',
            'timeLine': '',
            'populationNumber': [],
            'originalList': ['Control'],
            'log': {
                'results': [
                    {
                        'originalCell': 'Control',
                        'textPart': 'Control',
                        'textCleaned': 'Control', 
                        'textRepres': 'control group', 
                        'unitPart': '', 
                        'unitCleaned': '', 
                        'unitRepres': '', 
                        'unitRepprintresList': [], 
                        'timeLine': '', 
                        'type': 'group', 
                        'populationNumber': 0
                    }
                ]
            }
        },
        'col_header': {
            'text': 'supplementation', 
            'unit': [], 
            'type': 'unknown', 
            'timeLine': '', 
            'populationNumber': 29, 
            'originalList': ['Intervention (n = 29)'], 
            'log': {
                'results': [
                    {
                        'originalCell': 'Intervention (n = 29)', 
                        'textPart': 'Intervention', 
                        'textCleaned': 'Intervention', 
                        'textRepres': 'supplementation', 
                        'unitPart': '', 
                        'unitCleaned': '', 
                        'unitRepres': '', 
                        'unitRepresList': [], 
                        'timeLine': '', 
                        'type': 'unknown', 
                        'populationNumber': 29
                    }
                ]
            }
        },
        'value': [
            {
                'originalCell': '192(33.8)',
                'value': 192.0, 
                'unit': 'n', 
                'type': 'default'
            }, 
            {
                'originalCell': '192(33.8)', 
                'value': 33.8, 
                'unit': '%', 
                'type': 'default'
            }
        ]
    }
    """