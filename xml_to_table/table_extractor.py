# -*- coding: utf-8 -*- 
# from xml_to_table.cell_tagger import is_value, cell_tagging
from cell_tagger import is_value, cell_tagging
from lxml import etree
import pandas as pd
import re
from itertools import zip_longest
from ocrtable import tableextraction

def refine_html(html):
    html = re.sub('\<thead\>\n((.|\n)*)<\/thead\>\n', '',html)
    html = html.replace('<table border="1" class="dataframe">', '<table class="table table-hover kt-margin-b-0">')
    html = html.replace('<td>','<td class="text-center">')
    html = html.replace('<tr style="text-align: right;">','<tr>')
    return html

def processRow(ns, row):
    h_split_p = "[0-9]* (time) (\w+ )?[0-9]* (months|m|weeks)"
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
        if len(line_text) == 1:
            if bool(re.fullmatch(h_split_p, line_text[0])) and colSpan == 2:
                s_text = [m[0] for m in re.findall("([0-9]+ (time|months|m|weeks))", line_text[0])]
                split_lines = [[{"text" : t, "text_axis" : text_axis, "baseline" : baseline, "sup":b}] for t in s_text]
                rowInfos.extend(split_lines)
            else:
                rowInfos.extend([lines]*colSpan)
        else:
            rowInfos.extend([lines]*colSpan)
        
    return rowInfos, rowSpans

def hv_extract(tags_t, text_table):
    from operator import itemgetter
    from itertools import groupby
    result = []
    # ?�정?�요 ?�더 경계 구분 추�??�어????
    # --> ?�단 ?�외 규칙???�무 많아 경계?�식?��? ?�음.
    #row_h_border = 0
    #col_h_border = 0  
    try:
        r_len = len(tags_t)
        c_len = len(tags_t[0])
        srow = None
        ssrow = None
        sssrow = None

        for i in range(r_len):
            if tags_t[i][0] == 'srow':
                srow = text_table[i][0]
                ssrow = None
                sssrow = None
            elif tags_t[i][0] == 'ssrow':
                ssrow = text_table[i][0]
                sssrow = None
            elif tags_t[i][0] == 'sssrow':
                sssrow = text_table[i][0]
            elif tags_t[i][0] != "indent": #stub, v
                srow = None
                ssrow = None
                sssrow = None

            #row_stub_idx = [j for j in range(c_len) if not tags_t[i][j].startswith("v") and tags_t[i][j] != "empty"]
            row_stub_idx = []
            for j in range(c_len):
                if not tags_t[i][j].startswith("v") and tags_t[i][j] != "empty":
                    row_stub_idx.append(j)
                else:
                    break

            result_row=[]
            for j in range(c_len):
                cell_tag = tags_t[i][j]

                if cell_tag.startswith("v"):
                    row_header = [text_table[i][rs] for rs in row_stub_idx]
                    col_header=[]
                    for cs in range(i):
                        if tags_t[cs][j] == "stub":
                            col_header.append(text_table[cs][j])
                        else:
                            break
                    #col_header = [text_table[cs][j] for cs in range(i) if tags_t[cs][j] == "stub" and cs < i]

                    row_header = list(map(itemgetter(0), groupby(row_header)))
                    col_header = list(map(itemgetter(0), groupby(col_header)))

                    if srow is not None:
                        row_header.insert(0, srow)
                    if ssrow is not None:
                        row_header.insert(1, ssrow)
                    if sssrow is not None:
                        row_header.insert(2, sssrow)

                    row_header = list(map(itemgetter(0), groupby(row_header)))

                    row_header = [x for x in row_header if x !=""]
                    col_header = [x for x in col_header if x !=""]

                    result_row.append({"row_header": row_header, "col_header": col_header, "value": text_table[i][j]})
            result.append({"row":result_row})
        return result
    except:
        return []

def text_tag_split(rows):
    """
    text_table : 2d table
    tags: 2d table??tagging
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
            tag_row.append(is_value(text.strip()))
        text_table.append(text_table_row)
        tags.append(tag_row)
    return text_table, tags

def text_tag_split_2(list_2dtable):
    """
    text_table : 2d table
    tags: 2d table??tagging
    """
    list_2dtag = []
    for row in list_2dtable:
        list_tag = []
        for cell in list_2dtable:
            list_tag.append(is_value(cell))
    
    return list_tag

def srow_process(tags, rows):
    """
    srow/ssrow/indent tagging
    """
    for i in range(len(tags)):
        if tags[i][0] in ["stub", "indent"] and i>0:
            text_axis = 0
            next_axis = 0
            axis = []
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
                    #?�전 ?�스가 ??��졌을??  
                    elif 28 > text_axis > next_axis + 14:
                        continue
                    else:
                        if tags[i][0] == "indent" and tags[i+1][0] == "stub":
                            tags[i+1][0] = "indent"
    return tags


def srow_process2(tags, rows):
    """
    srow/ssrow/indent tagging
    """ 
    idt_depth = []
    tag_depth = ["indent"]
    d = 0

    for i, (rt, row) in enumerate(zip(tags, rows)): # row
        
        try:
            idt = int(row[0][0]["text_axis"])
        except:
            continue

        if rt[0] =="v" and len(idt_depth) == 0:
            continue
        
        if rt[0] =="stub" and len(idt_depth) == 0:
            idt_depth.append(idt)
            continue
            
        if idt_depth[d] + 14 < idt:
            if len(idt_depth)-1 == d:
                idt_depth.append(idt)
                tag_depth.insert(d, "s"*(d+1)+"row")
            if tags[i-1][0] == "stub" or tags[i-1][0] in tag_depth:
                tags[i-1][0] = tag_depth[d]
                tags[i][0] = tag_depth[d+1]
            d += 1
            
        elif idt_depth[d] - 14 > idt:
            for j in range(len(idt_depth)-1):
                if idt_depth[j] + 14 > idt:
                    d = j
                    tags[i][0] = tag_depth[d]
                    break
        else:
            if tags[i-1][0] != "empty":
                tags[i][0] = tags[i-1][0]
            continue

    return tags


def xml_to_table(xml_path):
    
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
            
            if block.get('blockType') == 'Table':

                ## EXTRACT UPCAPTION
                dict_upcaption_downcaption = {}
                table_blockidx = len(list_blockidx2lxmlidx) - 1
                
                list_up_block = []
                len_char_upblock = 0
                upblock_loop_counter = 0
                while len_char_upblock < 500 and table_blockidx - upblock_loop_counter >=0:
                    upblock_loop_counter += 1
                    prev_page_num, prev_block_num = list_blockidx2lxmlidx[table_blockidx - upblock_loop_counter]
                    blockforupcap = root[prev_page_num][prev_block_num]
                    
                    list_upblock_char = []
                    for charinfo in blockforupcap.iter("{" + ns + "}" + "charParams"):
                        word_first = charinfo.get('wordfirst')
                        if word_first != None and word_first == '1':
                            list_upblock_char.append(' ' + charinfo.text)
                        else:
                            if charinfo.text == None:
                                list_upblock_char.append("")
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

                ## EXTRACT DOWNCAPTION
                len_char_downblock = 0
                dict_upcaption_downcaption['downcaption'] = []
                ## EXTRACT DOWNCAPTION

                #try:
                axis = {"l" : block.get("l"),"r" : block.get("r"),"t" : block.get("t"),"b" : block.get("b")}
                rows=[]
                text_table=[]
                tags = []
                row_n=0
                for row in block.iter("{" + ns + "}" + "row"): # for all row
                    rowTexts, rowSpans = processRow(ns,row)

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
                                    #rows[row_n+j+1][rest_idx[i]] = rowTexts[i]
                                if row_n+j+1 < len(rows):
                                    rows[row_n+j+1][rest_idx[i]] = rowTexts[i]
                                else:
                                    rows.extend([["spans"]*len(rows[row_n+j]) for _ in range(max(rowSpans))])
                                    rows[row_n+j+1][rest_idx[i]] = rowTexts[i]
                    row_n+=1

                split_rows = []
                for row in rows:
                    len_set = set([len(a) for a in row if len(a) != 0])
                    if len(len_set) == 1 and len(row[0])>1:
                        for z in list(zip_longest(*[r for r in row], fillvalue=None)):
                            split_rows.append([[x] if x is not None else []  for x in list(z)])
                        #for a in zip(*row):
                        #    split_rows.append([[x] for x in list(a)])
                    #srow/indent merged case
                    elif len(row[0]) == 2 and int(row[0][0]["text_axis"]) + 14 < int(row[0][1]["text_axis"]):
                        for z in reversed(list(zip_longest(*[reversed(r) for r in row], fillvalue=None))):
                            split_rows.append([[x] if x is not None else []  for x in list(z)])
                    #indent/srow merged case
                    elif len(row[0]) == 2 and int(row[0][0]["text_axis"]) - 14 > int(row[0][1]["text_axis"]):
                        for z in list(zip_longest(*[r for r in row], fillvalue=None)):
                            split_rows.append([[x] if x is not None else []  for x in list(z)])
                    else:
                        split_rows.append(row)
                
                    # info -> 2d-table , info --> tags
                text_table, tags = text_tag_split(split_rows)
                
                BUFF = ''
                for row in text_table:
                    BUFF += '\t'.join(row) + '\n'
                print(BUFF)
                print("="*100)
                
                    # srow/ssrow/indent tag 변??
                    #tags = srow_process(tags, rows)             
                tags = srow_process2(tags, split_rows)

                    # table caption ?�거: 첫번�?row가 Table�??�작?�면 ?�당 row ??��
                while text_table[0][0].lower().startswith("table") or len(set(text_table[0])) == 1:
                    text_table = text_table[1:]
                    tags = tags[1:]


                    # hv_extract
                hv = hv_extract(tags, text_table)

                    

                tables["tableViewInfos"].append(
                        {
                            "table": text_table,
                            "table_html": None,
                            #"table_html": refine_html(pd.DataFrame(text_table).to_html()),
                            "axis" : axis,
                            "page" : page,
                            "hv": hv,
                            "table_type": None,
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
                        if charinfo.text == None:
                            list_downblock_char.append("")
                        else:
                            list_downblock_char.append(charinfo.text)
                        #list_downblock_char.append(charinfo.text)

                if len(list_downblock_char) == 0:
                    continue
                down_block = ''.join(list_downblock_char).strip()
                down_block = re.sub('[ ]+', ' ', down_block)
                dict_upcaption_downcaption['downcaption'].append(down_block)
                len_char_downblock += len(down_block)
                ## EXTRACT DOWNCAPTION
                

    return tables

def xml_to_table_2(xml_path, pdf_path):
    
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
    for tree_page in root.iter("{" + ns + "}" +"page"): # for all table/page
        page += 1
        axis = {}
        page_width, page_height = tree_page.attrib['width'], tree_page.attrib['height']

        ## EXTRACT CAPTION
        for blk_n, block in enumerate(tree_page.iter("{" + ns + "}" + "block")): # for all block
            list_blockidx2lxmlidx.append( (page-1, blk_n) )
            ## EXTRACT CAPTION

            # Table detection
            if block.get('blockType') == 'Table':

                ## EXTRACT UPCAPTION
                dict_upcaption_downcaption = {}
                table_blockidx = len(list_blockidx2lxmlidx) - 1
                
                list_up_block = []
                len_char_upblock = 0
                upblock_loop_counter = 0
                while len_char_upblock < 500 and table_blockidx - upblock_loop_counter >=0:
                    upblock_loop_counter += 1
                    prev_page_num, prev_block_num = list_blockidx2lxmlidx[table_blockidx - upblock_loop_counter]
                    blockforupcap = root[prev_page_num][prev_block_num]
                    
                    list_upblock_char = []
                    for charinfo in blockforupcap.iter("{" + ns + "}" + "charParams"):
                        word_first = charinfo.get('wordfirst')
                        if word_first != None and word_first == '1':
                            list_upblock_char.append(' ' + charinfo.text)
                        else:
                            if charinfo.text == None:
                                list_upblock_char.append("")
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

                ## EXTRACT DOWNCAPTION
                len_char_downblock = 0
                dict_upcaption_downcaption['downcaption'] = []
                ## EXTRACT DOWNCAPTION

                abbyyxml_str = etree.tostring(block)
                page_num = page - 1
                PIL_image = tableextraction.convertPdfToImage(pdf_path, 500, page_num, page_width, page_height)
                list_2dtable = tableextraction.getTableTSV(abbyyxml_str, PIL_image)
                list_2dtag = text_tag_split_2(list_2dtable)
                
                BUFF = ''
                for row in list_2dtable:
                    BUFF += '\t'.join(row) + '\n'
                print(BUFF)
                print("="*100)
                
                # hv_extract
                hv = hv_extract(list_2dtag, list_2dtable)

                tables["tableViewInfos"].append(
                        {
                            "table": text_table,
                            "table_html": None,
                            #"table_html": refine_html(pd.DataFrame(text_table).to_html()),
                            "axis" : axis,
                            "page" : page,
                            "hv": hv,
                            "table_type": None,
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
                        if charinfo.text == None:
                            list_downblock_char.append("")
                        else:
                            list_downblock_char.append(charinfo.text)
                        #list_downblock_char.append(charinfo.text)

                if len(list_downblock_char) == 0:
                    continue
                down_block = ''.join(list_downblock_char).strip()
                down_block = re.sub('[ ]+', ' ', down_block)
                dict_upcaption_downcaption['downcaption'].append(down_block)
                len_char_downblock += len(down_block)
                ## EXTRACT DOWNCAPTION
                

    return tables

if __name__ == "__main__":
    #print(xml_to_table('task1_30/xml_test/2010_S0021915010002431_NOS3 gene polymorphisms are as.xml'))
    #print(xml_to_table('task1_30/xml_test/2019_S1476927118307916_Conditional GWAS revealing gen.xml'))
    # print(xml_to_table('task2_error/2009_S0002870309003676_Association of genetic variant.xml'))
    #xml_to_table('task2_error/Gsе?.xml')
    #print(xml_to_table('task2_error/phy.xml'))
    # xml_to_table('./2009_S0002870309003676_Association of genetic variant.xml')
    xml_to_table_2('./2009_S0002870309003676_Association of genetic variant.xml', '2009_S0002870309003676_Association of genetic variant.pdf')
    # print(xml_to_table('./2009_S0002870309003676_Association of genetic variant.xml'))
