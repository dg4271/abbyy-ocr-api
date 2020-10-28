import numpy as np
from bs4 import BeautifulSoup
from collections import Counter

from .TableExtractionUtility import *


# [1] 표 인식 정보, 광학 문자 인식 정보 가져오기
def getTableInformation(in_abbyyxml_fpath):
    with open(in_abbyyxml_fpath, "r", encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, "html.parser")
        table_block = soup.find("block", attrs = {"blocktype":"Table"})
        list_char = table_block.findAll("charparams")

        table_l = int(table_block.attrs['l'])
        table_r = int(table_block.attrs['r'])
        table_b = int(table_block.attrs['b'])
        table_t = int(table_block.attrs['t'])

    out_dict_charid2info = dict()
    for i, char in enumerate(list_char, start=1):
        l = int(char.attrs['l']) - table_l
        r = int(char.attrs['r']) - table_l
        b = int(char.attrs['b']) - table_t
        t = int(char.attrs['t']) - table_t
        char = char.get_text()

        out_dict_charid2info[i] = {'l':l,'r':r,'b':b,'t':t, 'char':char, 'type':'char'}
    out_list_charid = list(out_dict_charid2info.keys())

    # table_width = table_r - table_l
    # table_height = table_b - table_t
    # out_table_spaceinfo = {'l':table_l, 'r':table_r, 't':table_t, 'b':table_b, 'width':table_width, 'height':table_height}
    
    return out_list_charid, out_dict_charid2info

# [2.1] 평균 문자 박스 크기와 너비 계산 및 박스 정규화
def calculateCharBoundingbox(in_list_charid, in_dict_charid2info):
    list_char_width = []
    dict_pid2boxsize = {}
    list_width = []
    list_height = []

    dict_id2charinfo = dict()
    list_xypoint = []
    for charid in in_list_charid:
        char_info = in_dict_charid2info[charid]
        list_width.append(char_info['r'] - char_info['l'])
        height = (char_info['b'] - char_info['t'])
        list_height.append(height)

        x, y = converyXY(char_info, 'cb')    
        char_info['x'] = x
        char_info['y'] = y
        
        char_info['box_size'] = (height)*(char_info['r'] - char_info['l'])

    out_mean_charbox_height = np.array(list_height).mean()
    out_mean_charbox_width = np.array(list_width).mean()
    out_mean_charbox_size = np.array([in_dict_charid2info[i]['box_size'] for i in in_list_charid]).mean()
    
    list_remove_idx = []
    for i in in_list_charid:
        char_info = in_dict_charid2info[i]
        in_dict_charid2info[i]['temp_b'] = in_dict_charid2info[i]['y']
        in_dict_charid2info[i]['temp_t'] = in_dict_charid2info[i]['y'] - out_mean_charbox_height / 2
        in_dict_charid2info[i]['temp_l'] = in_dict_charid2info[i]['l']
        in_dict_charid2info[i]['temp_r'] = in_dict_charid2info[i]['r']
        
        temp_size = char_info['box_size']
        if out_mean_charbox_size*8 < temp_size:
            print(i, char_info)
            list_remove_idx.append(i)
    
    for e in list_remove_idx:
        in_list_charid.remove(e)
        
    return out_mean_charbox_size, out_mean_charbox_width, out_mean_charbox_height

# [2.2] FLAT TOP-DOWN 클러스터링
def clusteringFlatTD(in_list_charid, in_dict_charid2info, in_mean_charbox_height, in_mode=0):
    if in_mode == 0:
        list_topsorted_charid = sorted(in_list_charid.copy(), key=lambda x:in_dict_charid2info[x]['t'])
    elif in_mode == 1:
        list_topsorted_charid = sorted(in_list_charid.copy(), key=lambda x:in_dict_charid2info[x]['temp_t'])
    
    out_list_sorted_charid = []

    while len(list_topsorted_charid) != 0:
        top_charid = list_topsorted_charid[0]
        list_topsorted_charid.remove(top_charid)

        list_included_charid = getTopCluster(top_charid, list_topsorted_charid, in_dict_charid2info, in_mean_charbox_height)
        for included_id in list_included_charid:
            list_topsorted_charid.remove(included_id)

        out_list_sorted_charid.append([top_charid] + list_included_charid)
    return out_list_sorted_charid

# [2.3] LEFT-RIGHT 클러스터링
def clusteringLR(in_list_topdown_charid, in_dict_charid2info, in_mean_charbox_width, in_mode):
    out_list_TDLR_charid = []
    temp_list = []
    for e_idx in range(len(in_list_topdown_charid)):
        if in_mode == 0:
            in_list_topdown_charid[e_idx] = sorted(in_list_topdown_charid[e_idx], key=lambda x: in_dict_charid2info[x]['l'])        
        elif in_mode == 1:
            in_list_topdown_charid[e_idx] = sorted(in_list_topdown_charid[e_idx], key=lambda x: in_dict_charid2info[x]['temp_l'])
        
        if len(in_list_topdown_charid[e_idx]) == 1:
            point_1 = in_list_topdown_charid[e_idx][0]
            out_list_TDLR_charid.append([point_1])
            continue
            
        prev_flagMerge = None        
        for i in range(0, len(in_list_topdown_charid[e_idx])-1, 1):            
            point_1 = in_list_topdown_charid[e_idx][i]
            point_2 = in_list_topdown_charid[e_idx][i+1]        
            # print('[*]', point_1, point_2)
            
            box_1 = in_dict_charid2info[point_1]
            box_2 = in_dict_charid2info[point_2]
            flagMerge = compareTwoLR(box_1, box_2, in_mean_charbox_width*2, in_mode)
            if prev_flagMerge == None:
                temp_list = []
                if flagMerge == True:
                    temp_list.append(point_1)
                    temp_list.append(point_2)
                else:
                    temp_list.append(point_1)
                    out_list_TDLR_charid.append(temp_list)
                    temp_list = []
                    temp_list.append(point_2)
            elif prev_flagMerge == True:
                if flagMerge == True:
                    temp_list.append(point_2)                
                else:
                    out_list_TDLR_charid.append(temp_list)
                    temp_list = []
                    temp_list.append(point_2)
            elif prev_flagMerge == False:
                if flagMerge == True:
                    temp_list.append(point_2)
                else:
                    out_list_TDLR_charid.append(temp_list)
                    temp_list = []
                    temp_list.append(point_2)
            prev_flagMerge = flagMerge
            
        if len(temp_list) !=0:
            out_list_TDLR_charid.append(temp_list)
    
    return out_list_TDLR_charid

# [2.4] Near 클러스터링
def clusteringNearPosition(in_list_clusterid, in_dict_clusterid2info, in_dict_charid2info, in_mean_charbox_size, in_mean_width, in_mean_height):    
    new_dict_clusterid2info = {}
    dict_cnt = 0

    new_list_temp_clusterid = in_list_clusterid.copy()
        
    cnt_merge = 1
    while cnt_merge > 0:
        cnt_merge = 0

        list_temp_clusterid = sorted(new_list_temp_clusterid, key=lambda x:in_dict_clusterid2info[x]['t'])
        new_list_temp_clusterid = []

        while len(list_temp_clusterid) > 0:
            select_cid = list_temp_clusterid[0]
            del list_temp_clusterid[0]

            # 후보 클러스터 리스트 받기
            list_candidate_clusterid = getCandidateCluster(select_cid, in_dict_clusterid2info, list_temp_clusterid, in_mean_width, in_mean_height)
                        
            if len(list_candidate_clusterid) > 1: # 병합 수행
                # 후보 클러스터 ID 리스트
                for e_cid in list_candidate_clusterid:
                    if e_cid in list_temp_clusterid:
                        list_temp_clusterid.remove(e_cid)
                
                # 병합 클러스터 생성
                merged_cluster_info = generateMergedCluster(list_candidate_clusterid, in_dict_clusterid2info, in_dict_charid2info)
                
                keyid = len(in_dict_clusterid2info) + 1
                in_dict_clusterid2info[keyid] = merged_cluster_info
                new_list_temp_clusterid.append(keyid)
                cnt_merge += 1
            else: # 병합 미수행
                new_list_temp_clusterid.append(select_cid)
    
    return new_list_temp_clusterid

# [3] 행렬 생성
## [3.1] 행 및 열 구분 작업 수행
def divideRowColumn(in_list_clusterid, in_dict_clusterid2info, in_mean_charbox_width):
    out_dict_rowcolid2clusterids = {}

    # 행 구분 작업 수행
    list_topsorted_clusterid = sorted(in_list_clusterid.copy(), key=lambda x: in_dict_clusterid2info[x]['t'])
    row = 1
    while len(list_topsorted_clusterid) != 0:
        top_cid = list_topsorted_clusterid[0]
        list_topsorted_clusterid.remove(top_cid)

        # 최좌상단 클러스터의 [TOP, BOTTOM] 구간 내부에 있는 클러스터 가져오기
        list_included_clusteridx = getRangeClusters_y(top_cid, list_topsorted_clusterid, in_dict_clusterid2info)
        for included_idx in list_included_clusteridx:
            list_topsorted_clusterid.remove(included_idx)

        out_dict_rowcolid2clusterids['row_{}'.format(row)] = [top_cid] + list_included_clusteridx
        for idx in [top_cid] + list_included_clusteridx:
            in_dict_clusterid2info[idx]['row'] = row
        row += 1
    
    # 열 구분 작업 수행
    list_leftsorted_clusterid = sorted(in_list_clusterid.copy(), key=lambda x: in_dict_clusterid2info[x]['l'])
    col = 1 
    while len(list_leftsorted_clusterid) != 0:
        left_cid = list_leftsorted_clusterid[0]
        list_leftsorted_clusterid.remove(left_cid)
        
        # 최좌상단 클러스터의 [LEFT, RIGHT] 구간 내부에 있는 클러스터 가져오기
        list_included_clusteridx = getRangeClusters_x(left_cid, list_leftsorted_clusterid.copy(), in_dict_clusterid2info, in_mean_charbox_width)
        for included_idx in list_included_clusteridx:
            list_leftsorted_clusterid.remove(included_idx)

        out_dict_rowcolid2clusterids['col_{}'.format(col)] = [left_cid] + list_included_clusteridx
        for idx in [left_cid] + list_included_clusteridx:
            in_dict_clusterid2info[idx]['col'] = col
        col += 1

    out_row_size, out_col_size = row - 1, col - 1
    
    # 하단 캡션 제거
    isContinue = True
    for i in range(out_row_size, 0, -1):
        key = 'row_{}'.format(i)
        if isContinue and len(out_dict_rowcolid2clusterids[key]) == 1:
            a_clusterid = out_dict_rowcolid2clusterids[key][0]
            str_cluster = in_dict_clusterid2info[a_clusterid]['str']
            
            print('[*]', str_cluster)
            in_list_clusterid.remove(a_clusterid)
            del out_dict_rowcolid2clusterids[key]
            out_row_size -= 1
        else:
            isContinue = False
            break
    
    # 상단 캡션 제거
    isContinue = True
    for i in range(1, out_row_size+1):
        key = 'row_{}'.format(i)
        if isContinue and len(out_dict_rowcolid2clusterids[key]) == 1:
            a_clusterid = out_dict_rowcolid2clusterids[key][0]
            str_cluster = in_dict_clusterid2info[a_clusterid]['str']
            
            print('[**]', str_cluster)
            in_list_clusterid.remove(a_clusterid)
            del out_dict_rowcolid2clusterids[key]
        else: 
            isContinue = False
            break
    
    # 셀ID 배열 초기화
    out_np_cellid_array = np.zeros((out_row_size+1, out_col_size+1)) -1
    start_row, end_row = 10000, -1
    for e_cid in in_list_clusterid:
        bbox = in_dict_clusterid2info[e_cid]
        out_np_cellid_array[bbox['row']][bbox['col']] = e_cid
        
        start_row = min(bbox['row'], start_row)
        end_row = max(bbox['row'], end_row)
    
    # cellid 배열 정보 채우기
    
    out_np_cellid_array = out_np_cellid_array[start_row:end_row+1,1:]
    out_row_size, out_col_size = out_np_cellid_array.shape    
    
    return out_dict_rowcolid2clusterids, out_np_cellid_array, out_row_size, out_col_size

# [3.2] 빈 칼럼 제거하기
def trimBlankCol(in_np_cellid_array):
    out_np_cellid_array = in_np_cellid_array.copy()
    row_size, col_size = out_np_cellid_array.shape
    for cnt in range(col_size):
        isBlank = True
        for idx in out_np_cellid_array[:,0]:
            if idx != -1:
                isBlank = False

        if isBlank:
            out_np_cellid_array = out_np_cellid_array[:,1:]        
            print('[*]', cnt)
        else:
            break
    
    row_size, col_size = out_np_cellid_array.shape
    
    return out_np_cellid_array, row_size, col_size

# [3.3] 빈셀 포함하여 완전한 배열 생성하기
def generateCellArray(in_dict_cellid2info, in_np_cellid_array, in_row_size, in_col_size):
    out_dict_cellid2info = in_dict_cellid2info.copy()
    out_np_cellid_array = in_np_cellid_array.copy()

    for i in range(in_row_size):
        for j in range(in_col_size):
            cellid = out_np_cellid_array[i][j]
            
            if cellid == -1:
                e_top, e_bottom, e_left, e_right = None, None, None, None
                # top, bottom 찾기
                for col_n in [e for e in range(in_col_size) if e != j]:
                    if out_np_cellid_array[i][col_n] != -1:
                        bbox = out_dict_cellid2info[out_np_cellid_array[i][col_n]]
                        e_top = bbox['t']
                        e_bottom = bbox['b']                    
                        break
                # left, right 찾기                    
                for row_n in [e for e in range(in_row_size) if e != i]:
                    if out_np_cellid_array[row_n][j] != -1:
                        bbox = out_dict_cellid2info[out_np_cellid_array[row_n][j]]
                        e_left = bbox['l']
                        e_right = bbox['r']
                        break
                
                key = len(out_dict_cellid2info)+1
                out_dict_cellid2info[key] = {'t':e_top, 'b':e_bottom, 'l':e_left, 'r':e_right, 'str':'', 'type':'blank', 'row':i, 'col':j}
                out_np_cellid_array[i][j] = key
            else:
                out_dict_cellid2info[cellid]['row'] = i
                out_dict_cellid2info[cellid]['col'] = j
    
    return out_dict_cellid2info, out_np_cellid_array

# [4] 구분선 인식 작업
def recognizeDivLine(in_paperjpg_fpath, in_list_charid, in_dict_charid2info):
    # PILLOW 이미지를 픽셀로
    if isinstance(in_paperjpg_fpath, str):
        img = Image.open(in_paperjpg_fpath)
    else:
        img = in_paperjpg_fpath
        
    pix = np.array(img)
    
    table_height, table_width = pix.shape[0], pix.shape[1]
    print('[*]', table_width, table_height)

    # 바운딩박스 제거하기
    bool_pix = np.zeros((pix.shape[0], pix.shape[1], 1))
    temp_size = 0
    for cid in in_list_charid:
        boundingbox = in_dict_charid2info[cid]
        left = boundingbox['l'] - 1
        right = boundingbox['r'] - 1
        bottom = boundingbox['b'] - 1
        top = boundingbox['t'] - 1
        
        bool_pix[top:bottom, left:right] = -1
        
        box_size = (right - left) * (bottom - top)
        temp_size += box_size
    newpix = np.concatenate((pix, bool_pix),axis=2)

    rowsize, colsize, ndim = newpix.shape

    # (COL 관련)범위 얻기
    list_all_conn_idx = []
    neg_cnt = 0
    curr_row_idx = None
    start_col_idx = None
    end_col_idx = None

    for row_idx in range(rowsize):
        flagRow = False
        list_conn_idx = []
        for col_idx in range(colsize):
            r,g,b,pos_state = newpix[row_idx,col_idx]
            if pos_state == -1:
                neg_cnt += 1
                continue
            
            if not flagRow and r < 50:
                flagRow = True
                curr_row_idx = row_idx
                start_col_idx = col_idx
            elif flagRow:
                if r < 50:
                    continue
                else:
                    flagRow = False
                    end_col_idx = col_idx
                    list_conn_idx.append((curr_row_idx, start_col_idx, end_col_idx))
        if flagRow:
            end_col_idx = col_idx
            list_conn_idx.append((curr_row_idx, start_col_idx, end_col_idx))
        list_all_conn_idx.extend(list_conn_idx)

    # (ROW 관련)범위 얻기
    start_curr_row_idx = None
    end_curr_row_idx = None
    temp_start_col_idx = None
    temp_end_col_idx = None

    stateContinue = -1
    out_list_divline = []
    for i, e in enumerate(list_all_conn_idx):
        curr_row_idx, start_col_idx, end_col_idx = e
        
        if end_col_idx - start_col_idx < 100:
            continue
        if stateContinue == -1:        
            start_curr_row_idx = curr_row_idx
            end_curr_row_idx = curr_row_idx
            temp_start_col_idx = start_col_idx
            temp_end_col_idx = end_col_idx
            
            stateContinue = 0
        elif stateContinue == 0:
            if start_curr_row_idx == curr_row_idx -1 and temp_start_col_idx == start_col_idx and temp_end_col_idx == end_col_idx:            
                end_curr_row_idx = curr_row_idx
            else:            
                # 이전 오브젝트 추가
                out_list_divline.append( {'l':temp_start_col_idx, 'r':temp_end_col_idx, 't':start_curr_row_idx, 'b': end_curr_row_idx, 'type':'line'} )
                
                # 새 오브젝트 초기화
                start_curr_row_idx = curr_row_idx
                end_curr_row_idx = curr_row_idx
                temp_start_col_idx = start_col_idx
                temp_end_col_idx = end_col_idx

    if stateContinue == 0:
        out_list_divline.append( {'l':temp_start_col_idx, 'r':temp_end_col_idx, 't':start_curr_row_idx, 'b': end_curr_row_idx, 'type':'line'} )
    
    out_list_divline.append({'l':1, 'r':table_width, 't':table_height-1, 'b':table_height, 'type':'line'})
    
    return out_list_divline

# [5] ROW HEADER 정리 작업
## [5.1] 구분선에 의한 셀 상태 할당
def getDLstate(in_list_divline, in_row_size, in_col_size, in_np_cellid_array, in_dict_cellid2info):
    out_np_dlstate_array = np.zeros((in_row_size, in_col_size)) -1
    out_set_dlstate = set()  
    
    dlstate_counter = Counter()
    
    if len(in_list_divline) >= 1:
        row_state = 0
        for i in range(0, in_row_size):
            for j in range(0, in_col_size):
                cellid = in_np_cellid_array[i][j]
                # print('[*]', cellid)
                # if cellid == -1:
                #    continue
                x = (in_dict_cellid2info[cellid]['l'] + in_dict_cellid2info[cellid]['r']) / 2
                y = (in_dict_cellid2info[cellid]['t'] + in_dict_cellid2info[cellid]['b']) / 2
                for dl_n, dline in enumerate(in_list_divline):
                    if (dline['l'] < x and x < dline['r']) and y < dline['b']:
                        in_dict_cellid2info[cellid]['divline'] = dl_n
                        out_np_dlstate_array[i][j] = dl_n
                        out_set_dlstate.add(dl_n)
                        dlstate_counter[dl_n] += 1
                        break
    
    return out_np_dlstate_array, out_set_dlstate, dlstate_counter

# [5.2] ROW HEADER 인식
def getRowHeader(dlstate_counter, set_dlstate, np_dlstate_array, in_row_size, in_col_size):
    list_sorted_dlstate = None
    
    most_dlstate = dlstate_counter.most_common()[0]
    most_key = most_dlstate[0]
    most_cnt = most_dlstate[1]
    all_cnt = in_row_size * in_col_size
    
    if most_cnt / all_cnt * 100 > 50:
        list_sorted_dlstate = list(sorted(set_dlstate))
        ###
        set_row = set()
        for i in range(in_row_size):
            for j in range(in_col_size):
                state_num = np_dlstate_array[i][j]
                if state_num == most_key:
                    set_row.add(i)

        set_remove_state = set()
        for i in set_row:
            for j in range(in_col_size):
                state_num = np_dlstate_array[i][j]
                set_remove_state.add(state_num)    
        
        for cand_key in set_remove_state:
            list_sorted_dlstate.remove(cand_key)

    return list_sorted_dlstate

# [5.3] ROW HEADER 상하 병합(열 내부 셀 병합)
def mergeUPDOWNCell(in_dict_cellid2info, in_np_dlstate_array, in_np_cellid_array, in_rowheader_idxlist, in_row_size, in_col_size):
    out_dict_cellid2info = in_dict_cellid2info.copy()
    out_np_cellid_array = in_np_cellid_array.copy()

    max_key = len(in_dict_cellid2info)
    set_gonecellid = set()

    dict_cellid2tempinfo = {}
    for i in range(0, in_row_size):
        for j in range(0, in_col_size):
            # 우측으로 탐색
            e_dlstate = in_np_dlstate_array[i][j]
            if e_dlstate in in_rowheader_idxlist:
                cellid = out_np_cellid_array[i][j]
                if cellid in set_gonecellid:
                    continue
                    
                list_temp = []
                list_temp.append(cellid)
                set_gonecellid.add(cellid)
                
                # 아래로 탐색
                row_idx = i + 1
                while row_idx < in_row_size:
                    ee_dlstate = in_np_dlstate_array[row_idx][j]
                    if ee_dlstate == e_dlstate:
                        list_temp.append(out_np_cellid_array[row_idx][j])
                        set_gonecellid.add(out_np_cellid_array[row_idx][j])
                    else:
                        break
                    row_idx += 1
                
                if len(list_temp) == 1:
                    continue
                            
                # Blank셀 이외의 셀에 할당 
                for e_cellid in list_temp[:-1]:                
                    bbox = out_dict_cellid2info[e_cellid]
                    e_row, e_col = bbox['row'], bbox['col'],
                    
                    max_key += 1
                    out_dict_cellid2info[max_key] = {'t':bbox['t'], 'b':bbox['b'], 'l':bbox['l'], 'r':bbox['r'], 
                                            'row':e_row, 'col':e_col,
                                            'str':'', 'type':'blank'}                                
                    out_np_cellid_array[e_row, e_col] = max_key
                
                # 병합셀 최하단에 할당            
                l,r,b,t = recalculateBoundingbox(list_temp, out_dict_cellid2info, 0)
                            
                cell_str = '<br>'.join([out_dict_cellid2info[e_cid]['str'] for e_cid in list_temp if out_dict_cellid2info[e_cid]['type'] != 'blank'])
                max_key += 1
                
                isBlank = False
                list_str = []
                for e_cid in list_temp:                
                    if out_dict_cellid2info[e_cid]['type'] != 'blank':
                        isBlank = True
                    else:
                        continue
                    list_str.append(out_dict_cellid2info[e_cid]['str'])
                
                cell_str = '<br>'.join(list_str)
                cell_type = 'blank' if isBlank == False else 'merged_cell'

                # print("[MERGE]",max_key, list_temp, cell_type)
                bbox = out_dict_cellid2info[list_temp[-1]]
                e_row, e_col = bbox['row'], bbox['col']
                out_dict_cellid2info[max_key] = {'list_cellid':list_temp, 
                                        'l':l, 'r':r, 'b':b, 't':t, 
                                        'row':e_row, 'col':e_col,
                                        'str':cell_str, 'type':cell_type}
                out_np_cellid_array[e_row, e_col] = max_key
    
    return out_dict_cellid2info, out_np_cellid_array

# [5.4] ROW HEADER 좌우 병합(행 내부 셀 병합)
def mergeLEFTRIGHTCell(in_dict_cellid2info, in_np_cellid_array, in_np_dlstate_array, in_rowheader_idxlist, in_row_size, in_col_size):
    out_dict_cellid2info = in_dict_cellid2info.copy()
    out_np_cellid_array = in_np_cellid_array.copy()
    max_key = len(out_dict_cellid2info)
    set_gonecellid = set()

    dict_cellid2tempinfo = {}
    for i in range(0, in_row_size):
        list_all_temp = []
        list_temp = []
        # (처음) 우측으로 탐색
        j = 0
        while j < in_col_size:
            e_dlstate = in_np_dlstate_array[i][j]
            col_idx = j + 1
            if not e_dlstate in in_rowheader_idxlist:
                j = col_idx
                continue
            list_temp.append(out_np_cellid_array[i][j])
                        
            # (연속) 우측으로 탐색
            while col_idx < in_col_size:
                ee_dlstate = in_np_dlstate_array[i][col_idx]
                if not ee_dlstate in in_rowheader_idxlist:
                    col_idx += 1
                    continue
                if ee_dlstate == e_dlstate:
                    list_temp.append(out_np_cellid_array[i][col_idx])
                else:                
                    break
                col_idx += 1
            list_all_temp.append(list_temp)
            list_temp = []
            j = col_idx 
            
        if len(list_all_temp) == 0:
            continue
        print('[*]', i, list_all_temp)
        for e_list_temp in list_all_temp:
            cell_length = len(e_list_temp)
            if cell_length < 2:
                continue        
            blank_cnt = 0
            normcell_idx = None
            for e_cellidx in e_list_temp:
                if out_dict_cellid2info[e_cellidx]['type'] == 'blank':
                    blank_cnt += 1
                else:
                    normcell_idx = e_cellidx
                print(out_dict_cellid2info[e_cellidx]['type'], end=' ')
            print(cell_length, blank_cnt)
                    
            # 모두 블랭크 셀이고 일반 셀이 1개라면 병합
            if cell_length - blank_cnt == 1:
                print('[**]', e_list_temp, cell_length, blank_cnt)
                for e_cellidx in e_list_temp:
                    if normcell_idx == e_cellidx:
                        continue
                    org_bbox = out_dict_cellid2info[e_cellidx]
                    norm_bbox = out_dict_cellid2info[normcell_idx]

                    max_key += 1
                    out_dict_cellid2info[max_key] = {'t':org_bbox['t'], 'b':org_bbox['b'], 'l':org_bbox['l'], 'r':org_bbox['r'], 
                                            'row':org_bbox['row'], 'col':org_bbox['col'],
                                            'str':norm_bbox['str'], 'type':'merged_cell2', 'refer':normcell_idx}
                    out_np_cellid_array[org_bbox['row'], org_bbox['col']] = max_key
                    print('[***] MERGE2', max_key, e_cellidx, normcell_idx)
            # 셀 리스트에 블랭크 셀이 있다면
            elif blank_cnt > 0:
                dict_norm2blanks = getNorm2blanks(e_list_temp, out_dict_cellid2info)
                                
                for e_normid, e_list_blankid in dict_norm2blanks.items():
                    for e_blankid in e_list_blankid:
                        blank_bbox = out_dict_cellid2info[e_blankid]
                        norm_bbox = out_dict_cellid2info[e_normid]

                        max_key += 1
                        out_dict_cellid2info[max_key] = {'t':blank_bbox['t'], 'b':blank_bbox['b'], 'l':blank_bbox['l'], 'r':blank_bbox['r'], 
                                                'row':blank_bbox['row'], 'col':blank_bbox['col'],
                                                'str':norm_bbox['str'], 'type':'merged_cell3', 'refer':e_normid}
                        out_np_cellid_array[blank_bbox['row'], blank_bbox['col']] = max_key
            # 아니면, 진행
            else:
                pass

    return out_dict_cellid2info, out_np_cellid_array

# [6] 인덴트 구분 작업 수행
def addIndentation(in_np_cellid_array, in_dict_cellid2info):
    list_range_idx = []
    for row_num, key in enumerate(in_np_cellid_array[0:,0]):
        if key < 0:
            pass
            # print('NONE')
        else:
            left = in_dict_cellid2info[key]['l']
            # print(left, '\t', in_dict_cellid2info[key]['str'])

            clusterFlag = False
            for n, (l_range, r_range, list_key) in enumerate(list_range_idx):
                if l_range <= left and left <= r_range:
                    mid_val = (l_range + r_range) / 2
                    clusterFlag = True
                    break

            if clusterFlag:            
                if mid_val < left:
                    list_range_idx[n][0] = left - 5
                    list_range_idx[n][2].append(key)
                elif mid_val > left:            
                    list_range_idx[n][1] = left + 5
                    list_range_idx[n][2].append(key)
                else:
                    list_range_idx[n][2].append(key)
            else:        
                list_range_idx.append( [left-3, left+3, []] )
                list_range_idx[len(list_range_idx)-1][2].append(key)

    sorted_list_range_idx = sorted(list_range_idx, key=lambda x:x[0])

    floor_counter = 0
    for e in sorted_list_range_idx:
        for key in e[2]:
            if in_dict_cellid2info[key]['type'] == 'blank':
                continue
            in_dict_cellid2info[key]['indent'] = floor_counter
        floor_counter += 1
    
    return

# [7] 출력 데이터 생성
def generateOutputTSV(in_np_cellid_array, in_dict_cellid2info):
    all_buff = []
    list_buff = []
    for row in in_np_cellid_array[0:,0:]:
        if row.max() < 0:
            continue
        for idx in row:
            if idx < 0:
                list_buff.append('<None>\t')
            else:
                if 'indent' in in_dict_cellid2info[idx]:
                    list_buff.append('<indent>'*in_dict_cellid2info[idx]['indent'] + '{}'.format(in_dict_cellid2info[idx]['str']) + '\t')
                else:
                    list_buff.append(in_dict_cellid2info[idx]['str'] + '\t')
        str_buff = ''.join(list_buff).strip()        
        if len(str_buff) != 0: 
            all_buff.append(''.join(list_buff))
        list_buff = []
    
    out_str_result = '\n'.join(all_buff)
    return out_str_result


# [7.1] 2D 테이블 리스트 생성
def generateTable2d(in_np_cellid_array, in_dict_cellid2info):
    
    list_table = []
    for row in in_np_cellid_array[0:,0:]:
        if row.max() < 0:
            continue
        list_row = []
        length_row = 0
        for idx in row:
            if idx < 0:
                list_row.append('')
            else:
                if 'indent' in in_dict_cellid2info[idx]:
                    list_row.append('<indent>'*in_dict_cellid2info[idx]['indent'] + '{}'.format(in_dict_cellid2info[idx]['str']))
                    length_row += len(in_dict_cellid2info[idx]['str'])
                else:
                    list_row.append(in_dict_cellid2info[idx]['str'])
                    length_row += len(in_dict_cellid2info[idx]['str'])
        
        if length_row != 0:
            list_table.append(list_row)

    return list_table
