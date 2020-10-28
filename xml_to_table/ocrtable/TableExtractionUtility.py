from PIL import Image, ImageDraw
from scipy.spatial import distance
import numpy as np

def visualizeBoundingbox(in_imgpath, in_list_id, in_dict_id2boxinfo, mode=0):
    out_im = Image.open(in_imgpath)
    
    draw = ImageDraw.Draw(out_im)
    for _id in in_list_id:
        boundingbox = in_dict_id2boxinfo[_id]
        if mode == 0:
            left = boundingbox['l']
            right = boundingbox['r']
            bottom = boundingbox['b']
            top = boundingbox['t']
        else:
            left = boundingbox['temp_l']
            right = boundingbox['temp_r']
            bottom = boundingbox['temp_b']
            top = boundingbox['temp_t']

        draw.rectangle((left, bottom, right, top), outline="purple")
    
    return out_im

def getTopCluster(in_tb_cluster_id, in_list_id, in_dict_id2boundingbox, in_mean_charbox_height, in_mode=0):
    if in_mode==0:
        fixed_top, fixed_bottom = in_dict_id2boundingbox[in_tb_cluster_id]['t'], in_dict_id2boundingbox[in_tb_cluster_id]['b']
    elif in_mode==1:
        fixed_top, fixed_bottom = in_dict_id2boundingbox[in_tb_cluster_id]['temp_t'], in_dict_id2boundingbox[in_tb_cluster_id]['temp_b']
    
    out_list_included_clusterid = []
    for idx in in_list_id:
        boundingbox = in_dict_id2boundingbox[idx]
        if in_mode==0:
            center_y = (boundingbox['t'] + boundingbox['b'])/2
        elif in_mode==1:
            center_y = (boundingbox['temp_t'] + boundingbox['temp_b'])/2
        if fixed_top <= center_y and center_y < fixed_bottom + in_mean_charbox_height:
            out_list_included_clusterid.append(idx)
        else:
            break
    
    return out_list_included_clusterid

def compareTwoLR(in_fixed_point, in_pivot_point, in_mean_charbox_width, in_mode):    
    if in_mode == 0:
        dist_bottom = distance.euclidean([in_fixed_point['r'], in_fixed_point['b']],
                                         [in_pivot_point['l'], in_pivot_point['b']])
        dist_top = distance.euclidean([in_fixed_point['r'], in_fixed_point['t']],
                                      [in_pivot_point['l'], in_pivot_point['t']])
    elif in_mode == 1:
        dist_bottom = distance.euclidean([in_fixed_point['r'], in_fixed_point['temp_b']],
                                         [in_pivot_point['l'], in_pivot_point['temp_b']])
        dist_top = distance.euclidean([in_fixed_point['r'], in_fixed_point['temp_t']],
                                      [in_pivot_point['l'], in_pivot_point['temp_t']])

    if dist_bottom <= dist_top:
        if dist_bottom <= in_mean_charbox_width:
            return True
    else:
        if dist_top <= in_mean_charbox_width:
            return True
    
    return False

def converyXY(in_boundingboxinfo, in_mode='lb'):
    if in_mode == 'lb':
        out_x, out_y = in_boundingboxinfo['l'], in_boundingboxinfo['b']
    elif in_mode == 'lt':
        out_x, out_y = in_boundingboxinfo['l'], in_boundingboxinfo['t']
    elif in_mode == 'rb':
        out_x, out_y = in_boundingboxinfo['r'], in_boundingboxinfo['b']
    elif in_mode == 'rt':
        out_x, out_y = in_boundingboxinfo['l'], in_boundingboxinfo['t']
    elif in_mode == 'cc':
        out_x, out_y = (in_boundingboxinfo['r'] + in_boundingboxinfo['l']) / 2, (in_boundingboxinfo['t'] + in_boundingboxinfo['b']) / 2
    elif in_mode == 'cb':
        out_x, out_y = (in_boundingboxinfo['r'] + in_boundingboxinfo['l']) / 2, in_boundingboxinfo['b']
    elif in_mode == 'lc':
        out_x, out_y = in_boundingboxinfo['l'], (in_boundingboxinfo['t'] + in_boundingboxinfo['b']) / 2
    elif in_mode == 'rc':
        out_x, out_y = in_boundingboxinfo['r'], (in_boundingboxinfo['t'] + in_boundingboxinfo['b']) / 2
    
    return out_x, out_y

def recalculateBoundingbox(in_list_id, in_dict_id2boundingbox, mode=0):
    out_min_l = 10000
    out_min_t = 10000
    out_max_r = -10000
    out_max_b = -10000        
    for idx in in_list_id:
        boundingbox = in_dict_id2boundingbox[idx]
        if mode == 0:
            out_min_l = min(out_min_l, boundingbox['l'])            
            out_min_t = min(out_min_t, boundingbox['t'])
            out_max_r = max(out_max_r, boundingbox['r'])
            out_max_b = max(out_max_b, boundingbox['b'])
        elif mode == 1:
            out_min_l = min(out_min_l, boundingbox['temp_l'])            
            out_min_t = min(out_min_t, boundingbox['temp_t'])
            out_max_r = max(out_max_r, boundingbox['temp_r'])
            out_max_b = max(out_max_b, boundingbox['temp_b'])
    
    return out_min_l, out_max_r, out_max_b, out_min_t

def getRangeClusters_x(in_lr_cluster_id, in_list_id, in_dict_id2boundingbox, in_mean_charbox_width):
    lr_boundingbox = in_dict_id2boundingbox[in_lr_cluster_id]
    temp_criteria = {} 
    temp_criteria['min_left'], temp_criteria['max_right'] = lr_boundingbox['l'], lr_boundingbox['r']
    temp_criteria['max_left'], temp_criteria['min_right'] = lr_boundingbox['l'], lr_boundingbox['r']
    
    out_list_included_clusteridx = []
    for idx in in_list_id:
        boundingbox = in_dict_id2boundingbox[idx]
        if boundingbox['l'] - temp_criteria['min_right'] > in_mean_charbox_width * 5:
            break

        if temp_criteria['min_left'] <= boundingbox['l'] and boundingbox['l'] < temp_criteria['max_right']:
            out_list_included_clusteridx.append(idx)

            temp_criteria['min_left'] = min(boundingbox['l'], temp_criteria['min_left'])
            temp_criteria['max_right'] = max(boundingbox['r'], temp_criteria['max_right'])

            temp_criteria['max_left'] = max(boundingbox['l'], temp_criteria['max_left'])
            temp_criteria['min_right'] = min(boundingbox['r'], temp_criteria['min_right'])
    
    return out_list_included_clusteridx

def getRangeClusters_y(in_tb_cluster_id, in_list_id, in_dict_id2boundingbox):
    fixed_top, fixed_bottom = in_dict_id2boundingbox[in_tb_cluster_id]['t'], in_dict_id2boundingbox[in_tb_cluster_id]['b']
    
    out_list_included_clusterid = []
    for idx in in_list_id:
        boundingbox = in_dict_id2boundingbox[idx]
        center_y = (boundingbox['t'] + boundingbox['b'])/2
        if fixed_top <= center_y and center_y < fixed_bottom:
            out_list_included_clusterid.append(idx)
        else:
            break
    
    return out_list_included_clusterid

## [5.4] 관련
def isBlankCell(in_cellid, in_dict_cellid2info):
    if in_dict_cellid2info[in_cellid]['type'] == 'blank':
        return True
    else:
        return False

# 설정 : cell_state(0=시작 상태, 1=정상셀 상태, 2=빈셀 상태)    
def getNorm2blanks(in_list_cellid, in_dict_cellid2info):
    e_normcellid = None
    cell_state = 0
    out_dict_norm2blanks = {}
    for e_cellid in in_list_cellid:
                
        ## 셀 상태 선택
        if cell_state == 0:
            if isBlankCell(e_cellid, in_dict_cellid2info) == True:
                cell_state = 0
                e_normcellid = None
            else:
                cell_state = 1
                e_normcellid = e_cellid
        elif cell_state == 1:
            if isBlankCell(e_cellid, in_dict_cellid2info) == True:
                cell_state = 2
            else:
                cell_state = 0
                e_normcellid = None
        elif cell_state == 2:
            if isBlankCell(e_cellid, in_dict_cellid2info) == True:
                cell_state = 2
            else:
                cell_state = 1
                e_normcellid = e_cellid
                
        ## 셀 상태에 따라 정보 처리
        if e_normcellid != None:
            if cell_state == 1:
                out_dict_norm2blanks[e_normcellid] = []
            elif cell_state == 2:
                out_dict_norm2blanks[e_normcellid].append(e_cellid)
        
    return out_dict_norm2blanks

def calculateDistance(p1, p2):
    # p1 박스, p2 박스 순서로 분리 배치
    if p1['r'] < p2['l']:
        dist_bottom = p2['l'] - p1['r']
        dist_top = dist_bottom        
    else:
        # p2 박스, p1 박스 순서로 분리 배치
        if p2['r'] < p1['l']:
            dist_bottom = p1['l'] - p2['r']
            dist_top = dist_bottom
        
        # p1 박스와 p2 박스가 겹쳐져서 배치          
        else:
            # 완전 겹침
            if p2['l'] < p1['r'] and p1['r'] < p2['r']:
                dist_bottom = 0
                dist_top = dist_bottom
            # 부분 겹침
            else:
                dist_bottom = 0
                dist_top = dist_bottom
    
    dist = min([dist_bottom, dist_top])
    
    return dist
    

def getCandidateCluster(in_select_cid, in_dict_clusterid2info, in_restcid_list, in_mean_width, in_mean_height):    
    out_list_candidate_clusterid = [in_select_cid]    
    p1_bbox = in_dict_clusterid2info[in_select_cid]
    dist = None
        
    for restcid in in_restcid_list:
        p2_bbox = in_dict_clusterid2info[restcid]
        if abs((p1_bbox['t'] + p1_bbox['b']) / 2 - (p2_bbox['t'] + p2_bbox['b']) / 2) < in_mean_height:
            dist = calculateDistance(p1_bbox, p2_bbox)
            if dist < in_mean_width:
                out_list_candidate_clusterid.append(restcid)

    return out_list_candidate_clusterid


def generateMergedCluster(in_list_candidate_clusterid, in_dict_clusterid2info, in_dict_charid2info):
    l,r,b,t = recalculateBoundingbox(in_list_candidate_clusterid, in_dict_clusterid2info, mode=0)
    
    list_temp_charid = []
    for clusterid in in_list_candidate_clusterid:
        list_temp_charid.extend(in_dict_clusterid2info[clusterid]['in_list_charid'])    
    list_temp_charid = sorted(list_temp_charid, key=lambda x:in_dict_charid2info[x]['l'])
    
    cluster_str = ''.join([in_dict_charid2info[e_charid]['char'] for e_charid in list_temp_charid])
    dict_cluster_info = {'in_list_charid':list_temp_charid, 'l':l, 'r':r, 'b':b, 't':t, 'str':cluster_str, 'type':'cluster'}
    
    return dict_cluster_info