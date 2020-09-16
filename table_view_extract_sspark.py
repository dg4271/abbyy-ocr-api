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
            "upcaption": [
                '~~',
                'table~~'
                ],
            "downcaption": [
                '~~',
                'table~~'
                ]
        }
    }
    """
    
    tables = {
        "tableViewInfos" : []
    }
    
    tree = etree.parse(xml_path)
    root = tree.getroot()
    ns = root.nsmap[None]
    
    ## EXTRACT CAPTION
    list_blockidx2lxmlidx = [] ##
    dict_upcaption_downcaption = None
    ## EXTRACT CAPTION
    
    page = 0
    for table in root.iter("{" + ns + "}" +"page"): # for all table/page
        page += 1
        axis = {}
        ## EXTRACT CAPTION
        for blk_n, block in enumerate(table.iter("{" + ns + "}" + "block")): # for all block            
            list_blockidx2lxmlidx.append( (page-1, blk_n) )
            ## EXTRACT CAPTION

            # Table detection
            rows=[]
            row_n=0
            if block.get('blockType') == 'Table':
                ## EXTRACT UPCAPTION
                dict_upcaption_downcaption = {}
                table_blockidx = len(list_blockidx2lxmlidx) - 1
                
                list_up_block = []
                len_char_upblock = 0
                upblock_loop_counter = 0
                while len_char_upblock < 500:
                    upblock_loop_counter += 1
                    prev_page_num, prev_block_num = list_blockidx2lxmlidx[table_blockidx - upblock_loop_counter]
                    blockforupcap = root[prev_page_num][prev_block_num]
                    
                    list_upblock_char = []
                    for charinfo in blockforupcap.iter("{" + ns + "}" + "charParams"):
                        word_first = charinfo.get('wordfirst')
                        if word_first != None and word_first == '1':
                            list_upblock_char.append(' ' + charinfo.text)
                        else:
                            list_upblock_char.append(charinfo.text)
                    
                    if len(list_upblock_char) == 0:
                        continue
                    up_block = ''.join(list_upblock_char).strip()
                    up_block = re.sub('[ ]+', ' ', up_block)
                    list_up_block.append(up_block)
                    len_char_upblock += len(up_block)
                list_up_block.reverse()
                dict_upcaption_downcaption['upcaption'] = list_up_block
                
                
                ## EXTRACT UPCAPTION
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
                
                ## EXTRACT DOWNCAPTION
                len_char_downblock = 0
                dict_upcaption_downcaption['downcaption'] = []
                ## EXTRACT DOWNCAPTION
                
                tables["tableViewInfos"].append(
                    {
                        "table_html": refine_html(pd.DataFrame(rows).to_html()),
                        "axis" : axis,
                        "page" : page,
                        "upcaption":dict_upcaption_downcaption['upcaption'],
                        "downcaption":dict_upcaption_downcaption['downcaption']
                    }
                )
            ## EXTRACT DOWNCAPTION
            elif dict_upcaption_downcaption != None and len_char_downblock < 500:
                
                list_downblock_char = []
                for charinfo in block.iter("{" + ns + "}" + "charParams"):
                    word_first = charinfo.get('wordfirst')
                    if word_first != None and word_first == '1':
                        list_downblock_char.append(' ' + charinfo.text)
                    else:
                        list_downblock_char.append(charinfo.text)

                if len(list_downblock_char) == 0:
                    continue
                down_block = ''.join(list_downblock_char).strip()
                down_block = re.sub('[ ]+', ' ', down_block)
                dict_upcaption_downcaption['downcaption'].append(down_block)
                len_char_downblock += len(down_block)
            ## EXTRACT DOWNCAPTION

    return tables