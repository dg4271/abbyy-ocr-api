from lxml import etree
import pandas as pd
import re

def refine_html(html):
    html = re.sub('\<thead\>\n((.|\n)*)<\/thead\>\n', '',html)
    html = html.replace('<table border="1" class="dataframe">', '<table class="table table-hover kt-margin-b-0">').replace('<td>','<td class="text-center">').replace('<tr style="text-align: right;">','<tr>')
    return html

def processRow(ns, row):
    rowTexts = []
    rowSpans = []
    for cell in row.iter("{" + ns + "}" + "cell"): # for all cell
        # rowSpan & colSpan
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

        # text of cell
        text = ""
        for line in cell[0][0]:  # <cell> <text> <par> <line> </par> </text> </cell>
            text += "".join([char.text for char in line[0]]) # <line> <formatting> <charParams>

        rowTexts.extend([text]*colSpan)
    
    return rowTexts, rowSpans

def xml_to_list(xml_path):
    """
    ouput : 
    {
        "table1" : {
            "table": [[], []] --> header 분리해서 출력?
            "page": 1
            "axis": {
                "l" : 1, 
                "r" : 2, 
                "t" : 4,
                "b" : 3
            }
        }
    }
    """
    
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
            # Table detection
            rows=[]
            row_n=0
            if block.get('blockType') == 'Table':
                axis = {
                    "l" : block.get("l"),
                    "r" : block.get("r"),
                    "t" : block.get("t"),
                    "b" : block.get("b")
                }
                for row in block.iter("{" + ns + "}" + "row"): # for all row
                    rowTexts, rowSpans = processRow(ns,row)
                    
                    # set rowTexts               
                    if row_n >= len(rows):
                        rows.append(rowTexts)
                    else:
                        for t in rowTexts:
                            for j in range(len(rows[row_n])):
                                if rows[row_n][j] == "spans":
                                    rows[row_n][j] = t
                                    break

                    # set Span?
                    if sum(rowSpans) > 0 :
                        span_rows = [['spans']*len(rowTexts) for _ in range(max(rowSpans))]
                        for i in range(len(rowSpans)):
                            if rowSpans[i]>0:
                                for j in range(rowSpans[i]):
                                    span_rows[j][i] = ""
                        rows.extend(span_rows)
                        #rowSpans = []
                    row_n += 1
                
                tables["tableViewInfos"].append(
                    {
                        "table_html": refine_html(pd.DataFrame(rows).to_html()),
                        "axis" : axis,
                        "page" : page
                    }
                )

    return tables