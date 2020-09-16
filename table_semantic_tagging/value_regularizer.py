import re


class ValueRegularizer():
    def __init__(self):
        p_value_header = "[pP][12]?([ \-]?[vV]alue[s]?( for intervention)?|( for |-)(linear )?trend( [a-z ]+|1)?| \(hot voxel\)| \(chi square\))?[*1-8a-hty]?( -)?"
        self.p_value_header= "(^{}| {})$".format(p_value_header, p_value_header)
        
        self.pre_symbol = "(([ \\\\«~#\^|•:■/*;,'’!_di-km)][ \\\\«~#\^|•■</*:;,'’!_di-km)]*[hJX \^]*|GFR|(Md)?-?[ •:;'m]+|1-[ *:]+)*)"
        self.post_symbol = "(([•■;\^\*%#&$§_\-<‘’”“\"',. ()|\\\\]|[+A-CGPTXZa-flmnstwxy])*|[(][a-zR. \-]+[)])"

        self.p_value_tag = "(Interaction)? ?[pP]( value)? ?[—=<>]"
        _n_type = "([<>+\-±—§~]|min|max|up to pH|SD|%s|([nr]|rho) ?[ =<>] ?[—\-]?|T:|-? ?\$|-50[GT]{,2} =)?" % (self.p_value_tag)
        _number = "0[,\-][0-9]+|[1-9]-[0-9]{2,}|[0-9]+-0[0-9]+|[0-9 ]*[0-9]-[0-9]|[0-9 ]+[0-9]+-[0-9]{2}|\.?[0-9]"
        _power = "[0-9.'’\^][0-9.'’\^\-]* ?([xX*] ?10|[Ee])-?[0-9]+"
        _num_w_error = "([0-9lo]|Q-|i[.0-9]|(\.|- ?)[0-9])[ 0-9lOQSf.,'’:\^]*[0-9lOQSf.'’:\^]+"
        _numeric = " ?(%s|%s|%s)[*]*" %(_power, _num_w_error, _number)

        _unit1 = "°C|%|I ?U(/d)?.*|(mg|mcg|MCU)/[dL]|[mp]?g|[mnp]m[°o]l/L|mL/min|kcal/mL|k([jl]|cal)?"
        _unit2 = "[(]IgG[12][)]|RAE|HD( and PD)?|PD|py|servings/(week|day).*|days?|[yY]ears|-?months?"
        _unit3 = "sibling/related|unrelated|light|moderate|bar|min|h( oral)?"
        _sex = "(% )?\(?(wo)?men\)?|(fe)?male|[(][MF][)]"
        _etc_unit = "% CM|m?g/dia( TTS)?|mg i\.m\.|/?semanas?|kg( peso)?|% f (fuerza|area|volumen) [a-z0-9 ]+|with( and|out body mass reduction)"
        _unit = "{}|{}|{}|{}|{}".format(_unit1, _unit2, _unit3, _sex, _etc_unit)

        value_pattern0 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(0, _n_type, _numeric, _unit)
        value_pattern1 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(1, _n_type, _numeric, _unit)
        value_pattern2 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(2, _n_type, _numeric, _unit)
        value_pattern3 = "(?P<type{0}>{1})(?P<numeric{0}>{2}) ?(?P<unit{0}>{3})?".format(3, _n_type, _numeric, _unit)
        
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
            value_dic["unit"] = "count"
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
                    "originalCell": t,
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
                    if result[i]["unit"] != '%':
                        result[i]["type"] = "count"
            elif len(result) == 3 and sep == '/' and result[2]["unit"] == '%': # N1/N2 N3%인 경우, 첫 번째 N은 대상자수, 두 번째 N은 전체 대상자수
                if result[0]["value"] > result[1]["value"]:
                    result[0], result[1] = result[1], result[0]
                result[0]["unit"] = "count"
                result[1]["unit"] = "count"
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
    
    def regularize_value_with_header(self, header_and_value):
        row_header = header_and_value["row_header"]
        col_header = header_and_value["col_header"]
        number_of_values = None
        
        is_p_value = False
        if (col_header and re.search(self.p_value_header, col_header[-1])) \
            or (row_header and re.search(self.p_value_header, row_header[-1])) \
            or (len(col_header) > 1 and re.search(self.p_value_header, col_header[0])) \
            or (len(row_header) > 1 and re.search(self.p_value_header, row_header[0])):
            is_p_value = True
            
        values = self.regularize_value(header_and_value["value"], number_of_values)
        
        if is_p_value and len(values) == 1 and values[0]["type"] != "range" and values[0]["value"] <= 1:
            values[0]["unit"] = "p_value"
            is_significant = values[0]["type"] == "less"
            values[0]["significant"] = is_significant
        elif header_and_value["value"].lower() == "ns":
            values = [{
                "value": None,
                "unit": "p_value",
                "significant": False
            }]
        
        return values


if __name__ == "__main__":
    """
    - input: value 문자열 // 희원 주임이 주는 데이터에 따라 input 변경될 수 있음
    - output: 정규화된 value 딕셔너리
    
    참고자료
    <정의된 value 타입> *더 추가될 예정*
    "range"         : "value"에 [최솟값, 최댓값]으로 저장되어 있음.
    "mean           : 평균
    "SD"            : 표준편차
    "less"          : 작음
    "less or equal" : 작거나 같음
    "more"          : 큼
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
        "row_header": ['p-Valueb'],
        "col_header": ['Intervention (n = 29)'],
        "value": "<0.0001"
    }
    print(vr.regularize_value_with_header(test))
    """
    출력결과
    [
      {
        'originalCell': '<0.0001',
        'value': 0.0001,
        'unit': 'p_value',
        'type': 'less',
        'significant': True
      }
    ]
    """