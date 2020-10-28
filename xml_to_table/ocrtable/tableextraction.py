import os
import glob
import logging
import argparse
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from PIL import Image, ImageDraw
from matplotlib.pyplot import imshow
from pdf2image import convert_from_path

from scipy.spatial import distance

from collections import Counter
import numpy as np
import scipy

from .TableExtractionHelper import *


'''
pdf page를 image로 변환하기
    input : load_pdf_fpath, save_imgpath, page_num, page_width, page_height
    output : page PIL image
'''
def convertPdfToImage(load_pdf_fpath, save_imgpath, page_num, page_width, page_height):
    if page_height > page_width:
        page_width, page_height = page_height, page_width
    pages = convert_from_path(load_pdf_fpath, 500, first_page=page_num ,last_page=page_num ,size=(page_width, page_height))
    
    return pages[0]

'''
    abbyy 테이블 결과를 받아 테이블 추출 결과 반환한다.
    input : table xml(str)
    output : table tsv(str)
'''
def getTableTSV(abbyyxml_fpath, PIL_image):
    # 1. 표 인식 정보, 광학 문자 인식 정보 가져오기
    list_charid, dict_charid2info = getTableInformation(abbyyxml_fpath)
    
    # 2.1. 평균 문자 박스 크기와 너비 계산 및 박스 정규화
    mean_charbox_size, mean_charbox_width, mean_charbox_height = calculateCharBoundingbox(list_charid, dict_charid2info)
    
    # [2.2] FLAT TOP-DOWN 클러스터링
    list_topdown_charid = clusteringFlatTD(list_charid, dict_charid2info, mean_charbox_height / 3, in_mode=1)

    # [2.3.1] LEFT-RIGHT 클러스터링
    list_TDLR_charid = clusteringLR(list_topdown_charid, dict_charid2info, mean_charbox_width, in_mode=1)

    # [2.3.2] 클러스터링 사전 및 리스트 생성
    dict_clusterid2info = {}
    cnt = 1
    for e_list_cid in list_TDLR_charid:
        l,r,b,t = recalculateBoundingbox(e_list_cid, dict_charid2info, mode=0)
        cluster_str = ''.join([dict_charid2info[ee_cid]['char'] for ee_cid in e_list_cid])
        dict_clusterid2info[cnt] = {'in_list_charid':e_list_cid, 'l':l, 'r':r, 'b':b, 't':t, 'str':cluster_str, 'type':'cluster'}
        cnt += 1
    list_clusterid = list(dict_clusterid2info.keys())

    # [2.4] Near 클러스터링
    list_new_clusterid = clusteringNearPosition(list_clusterid, dict_clusterid2info, dict_charid2info, 
                                        mean_charbox_size, mean_charbox_width, mean_charbox_height)
    list_clusterid, dict_clusterid2info = list_new_clusterid, dict_clusterid2info

    # [3] 행렬 생성
    ## [3.1] 행 및 열 구분 작업 수행
    dict_rowcolid2clusterids, np_cellid_array, row_size, col_size = divideRowColumn(list_clusterid, dict_clusterid2info, mean_charbox_width)
    
    # [3.2] 빈 칼럼 제거하기
    np_cellid_array, row_size, col_size = trimBlankCol(np_cellid_array)

    # [3.3] 빈셀 포함하여 완전한 배열 생성하기
    dict_cellid2info, np_cellid_array = generateCellArray(dict_clusterid2info, np_cellid_array, row_size, col_size)

    # [4] 구분선 인식 작업
    list_divline = recognizeDivLine(PIL_image, list_charid, dict_charid2info)

    # [5] ROW HEADER 정리 작업
    ## [5.1] 구분선에 의한 셀 상태 할당
    np_dlstate_array, set_dlstate, dlstate_counter = getDLstate(list_divline, row_size, col_size, np_cellid_array, dict_cellid2info)

    # [5.2] ROW HEADER 인식
    rowheader_idxlist = getRowHeader(dlstate_counter, set_dlstate, np_dlstate_array, row_size, col_size)


    if rowheader_idxlist is not None:
        # [5.3] ROW HEADER 상하 병합(열 내부 셀 병합)
        dict_cellid2info, np_cellid_array = mergeUPDOWNCell(dict_cellid2info, np_dlstate_array, np_cellid_array,
                                                        rowheader_idxlist, row_size, col_size)

        # [5.4] ROW HEADER 좌우 병합(행 내부 셀 병합)        
        dict_cellid2info, np_cellid_array = mergeLEFTRIGHTCell(dict_cellid2info, np_cellid_array, np_dlstate_array,
                                                           rowheader_idxlist, row_size, col_size)

    # 6. 인덴트 구분 작업 수행
    addIndentation(np_cellid_array, dict_cellid2info)

    # 7. 출력 2d 테이블 생성        
    list_2d_table = generateTable2d(np_cellid_array, dict_cellid2info)
        
    return list_2d_table

if __name__ == '__main__':
    list_2d_table = getTableTSV('../data/TableDetection/metabolic/cropped_table_xml/0028_2009_S0021915008007727_Association between Creactive _001.xml',
                      '../data/TableDetection/metabolic/cropped_table_image/0028_2009_S0021915008007727_Association between Creactive _001.jpg'
                     )

    print(list_2d_table)

    print("="*100)
    BUFF = ''
    for row in list_2d_table:
        BUFF += '\t'.join(row) + '\n'

    print(BUFF)