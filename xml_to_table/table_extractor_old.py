# -*- coding: utf-8 -*- 
from xml_to_table.cell_tagger import is_value, cell_tagging
from lxml import etree
import pandas as pd
import re

def refine_html(html):
    html = re.sub('\<thead\>\n((.|\n)*)<\/thead\>\n', '',html)
    html = html.replace('<table border="1" class="dataframe">', '<table class="table table-hover kt-margin-b-0">')
    html = html.replace('<td>','<td class="text-center">')
    html = html.replace('<tr style="text-align: right;">','<tr>')
    return html

def processRow(ns, row):
    rowInfos = []
    rowSpans = []
    for cell in row.iter("{" + ns + "}" + "cell"): # for all cell
        # rowSpan & colSpan
        rowSpan = 0
        colSpan = 1
        if cell.get("rowSpan") is not None:
            rowSpan = int(cell.get("rowSpan"))-1
        if cell.get("colSpan") is not None:
            colSpan = int(cell.get("colSpan"))
        rowSpans.extend([rowSpan]*colSpan)
        #bottomBorder
        
        # text of cell
        lines = []
        line_text = []
        for line in cell.iter("{" + ns + "}" + "line"):  # <cell> <text> <par> <line> </par> </text> </cell>
            text = ""
            for char in line.iter("{" + ns + "}" + "charParams"):
                if char.text is not None:
                    text += char.text
            line_text.append(text)
            text_axis = line.get("l")
            baseline = line.get("baseline")
            
            lines.append({"text" : text, "text_axis" : text_axis, "baseline" : baseline})
        
        rowInfos.extend([lines]*colSpan)
    
    return rowInfos, rowSpans

def hv_extract(tags_t, text_table):
    from operator import itemgetter
    from itertools import groupby
    result = []
    
    # 헤더 경계 구분 추가되어야 함
    r_len = len(tags_t)
    c_len = len(tags_t[0])
    srow = None
    ssrow = None

    use_indent = False
    use_srow = False
    for i in range(r_len):
        if tags_t[i][0] == 'srow':
            srow = text_table[i][0]
        elif tags_t[i][0] == 'ssrow':
            ssrow = text_table[i][0]
        elif use_indent and tags_t[i][0] != "indent":
            srow = None
            ssrow = None

        row_stub_idx = [j for j in range(c_len) if not tags_t[i][j].startswith("v") and tags_t[i][j] != "empty"]

        for j in range(c_len):
            cell_tag = tags_t[i][j]

            if cell_tag.startswith("v"):
                row_header = [text_table[i][rs] for rs in row_stub_idx if rs < j]
                col_header = [text_table[cs][j] for cs in range(i) if tags_t[cs][j] == "stub" and cs < i]

                row_header = list(map(itemgetter(0), groupby(row_header)))
                col_header = list(map(itemgetter(0), groupby(col_header)))

                if srow is not None:
                    row_header.insert(0, srow)
                if ssrow is not None:
                    row_header.insert(1, ssrow)

                row_header = list(map(itemgetter(0), groupby(row_header)))

                row_header = [x for x in row_header if x !=""]
                col_header = [x for x in col_header if x !=""]

                result.append({"row_header": row_header, "col_header": col_header, "value": text_table[i][j]})
    return result


def text_tag_split(rows):
    """
    text_table : 2d table
    tags: 2d table의 tagging
    """
    text_table=[]
    tags = []
    for row in rows:
        text_table_row = []
        tag_row = []
        for cell in row:
            text = ""
            text_axis = 0
            for line in cell: 
                text += " " + line["text"]
                if text_axis ==0:
                    text_axis = int(line["text_axis"])
            text_table_row.append(text.strip())
            tag_row.append(cell_tagging(text.strip()))
        text_table.append(text_table_row)
        tags.append(tag_row)
    return text_table, tags

def srow_process(tags, rows):
    """
    srow/ssrow/indent tagging
    """
    for i in range(len(tags)):
        if tags[i][0] in ["stub", "indent"] and i>0:
            text_axis = 0
            next_axis = 0
            for line in rows[i][0]:
                if text_axis ==0:
                    text_axis = int(line["text_axis"])

                if i+2 <= len(tags):
                    for line in rows[i+1][0]:
                        if next_axis ==0:
                            next_axis = int(line["text_axis"])

                    if text_axis + 14 < next_axis:
                        if tags[i][0] == "stub" and tags[i+1][0] == "stub":
                            tags[i][0] = "srow"
                            tags[i+1][0] = "indent"
                        elif tags[i][0] == "srow" and tags[i+1][0] == "stub":
                            tags[i][0] = "ssrow"
                            tags[i+1][0] = "indent"

                                #이전 뎁스 일때    
                    elif text_axis > next_axis + 14:
                        continue
                    else:
                        if tags[i][0] == "indent" and tags[i+1][0] == "stub":
                            tags[i+1][0] = "indent"
    return tags


def xml_to_table(xml_path):
    
    tables = {
        "tableViewInfos" : []
    }
    tree = etree.parse(xml_path)
    root = tree.getroot()
    ns = root.nsmap[None]
    
    page = 0
    for table in root.iter("{" + ns + "}" +"page"): # for all table/page
        page += 1
        axis = {}
        for block in table.iter("{" + ns + "}" + "block"): # for all block
            axis = {
                "l" : block.get("l"),
                "r" : block.get("r"),
                "t" : block.get("t"),
                "b" : block.get("b")
            }
            # Table detection
            rows=[]
            text_table=[]
            tags = []
            row_n=0
            if block.get('blockType') == 'Table':
                axis = {"l" : block.get("l"),"r" : block.get("r"),"t" : block.get("t"),"b" : block.get("b")}
                for row in block.iter("{" + ns + "}" + "row"): # for all row
                    rowTexts, rowSpans = processRow(ns,row)
                    #print(rowTexts)
                    if row_n >= len(rows):
                        rows.append(rowTexts)
                        if sum(rowSpans)>0:
                            rows.extend([["spans"]*len(rowSpans) for _ in range(max(rowSpans))])
                            for i in range(len(rowSpans)):
                                for j in range(rowSpans[i]):
                                    rows[row_n+j+1][i] = rowTexts[i]
                    else:
                        rest_idx = [i for i, value in enumerate(rows[row_n]) if value == "spans"]

                        for i in range(len(rest_idx)):
                            rows[row_n][rest_idx[i]] = rowTexts[i]
                            for j in range(rowSpans[i]):
                                rows[row_n+j+1][rest_idx[i]] = rowTexts[i]
                    row_n+=1   
                
                #info -> split lines(필요한 경우)
                
                # info -> 2d-table , info --> tags
                text_table, tags = text_tag_split(rows)               

                # srow/ssrow/indent tag 변환
                tags = srow_process(tags, rows)
                # hv_extract
                hv = hv_extract(tags, text_table)
                #동근 output input: text_table, caption


                tables["tableViewInfos"].append(
                    {
                        "table": text_table,
                        "table_html": None,
                        #"table_html": refine_html(pd.DataFrame(text_table).to_html()),
                        "axis" : axis,
                        "page" : page,
                        "hv": hv,
                        "table_type": None
                    }
                )
    return tables

if __name__ == "__main__":
    print(xml_to_table("../data/xml/2008_S0002929708001742_On the Replication of Genetic .xml"))