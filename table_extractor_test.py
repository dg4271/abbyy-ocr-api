# -*- coding: utf-8 -*- 

from lxml import etree

def is_value(text):
    len_t = len(text.replace(" ",""))
    if len_t == 0:
        return 0
        
    len_int = 0
    for char in text.split():
        try:
            float(char)
            len_int += len(char)
        except:
            continue
    if len_int/len_t > 0.7:
        return 1
    else:
        return 0
    
    
# Load XML
def xml_to_list(xml_path):
    #file
    #tree = etree.parse(xml_path)
    #root = tree.getroot()

    root = etree.fromstring(xml_path)
    
    for table in root:
        for block in table:
            if block.tag.endswith("block"):
                rows=[]
                row_n=0
                for row in block:
                    if row.tag.endswith("row"):
                        row_t=[]
                        rowSpans = []
                        for cell in row:
                            rowSpan = 0
                            colSpan = 1
                            #width = cell.get("width")                #너비 일단은 사용안함 (좌표용)
                            if cell.get("rowSpan") is not None:
                                rowSpan = int(cell.get("rowSpan"))-1
                            if cell.get("colSpan") is not None:
                                colSpan = int(cell.get("colSpan"))
                                #width = float(width)/float(colSpan)  #너비 일단은 사용안함 (좌표용)
                            rowSpans.extend([rowSpan]*colSpan)
                            #align = cell[0][0].get("align")          #정렬 일단은 사용안함 (좌표용)
                            text = ""
                            for line in cell[0][0]:
                                for char in line[0]:
                                    text += char.text
                            row_t.extend([text]*colSpan)

                        if row_n >= len(rows):
                            rows.append(row_t)
                        else:
                            for t in row_t:
                                for j in range(len(rows[row_n])):
                                    if rows[row_n][j] == "spans":
                                        rows[row_n][j] = t
                                        break

                        if sum(rowSpans) > 0 :
                            span_rows = [['spans']*len(row_t) for _ in range(max(rowSpans))]
                            for i in range(len(rowSpans)):
                                if rowSpans[i]>0:
                                    for j in range(rowSpans[i]):
                                        span_rows[j][i] = ""
                            rows.extend(span_rows)
                            rowSpans = []
                        row_n+=1
    return rows

def split_header(rows):
    from itertools import groupby
    colh_len = 0 # is_value로 판단 
    rowh_len = 0 # is_value로 판단
    for i in range(len(rows)):
        val = [is_value(v) for v in rows[i]]
        if sum(val) == 0:
            colh_len += 1
        else:
            rn = [len(list(a[1])) for a in groupby(val) if a[0]==0][0]
            if rn > rowh_len:
                rowh_len = rn
    col_header = [x for x in rows[0]]
    for i in range(1,colh_len):
        for j in range(len(rows[i])):
            if col_header[j] != "":
                col_header[j] += "/" + rows[i][j] #header의 depth 구분
            else:
                col_header[j] += rows[i][j]

    data = [row[rowh_len:] for row in rows[colh_len:]]
    row_header = [t[0] for t in rows[colh_len:]]
    
    return col_header, row_header, data

def xml_to_table(xml_path):
    return split_header(xml_to_list(xml_path))

if __name__ == "__main__":
    col_header, row_header, data = xml_to_table("data/table_xml_test.xml")
    print(col_header)
    print(row_header)
    print(data)
