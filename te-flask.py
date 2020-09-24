# -*- coding: utf-8 -*- 

from flask import Flask, request, jsonify, Response
import logging
import json

from abbyy.AbbyyOnlineSdk import AbbyyOnlineSdk
from abbyy.cjProcess import *


import table_extractor_test
import table_view_extract
import preKB_mapper
from xml_to_table.table_extractor import * 
from table_classifier.tableClassifier import is_collect_table, get_type
from table_classifier.preprocessing import get_header_value_info_new



# Flask
UPLOAD_FOLDER = '/data1/saltlux/CJPoc/table-extraction/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
logging.basicConfig(level = logging.INFO)

# Abbyy
processor = None
fileName_docID_dict = preKB_mapper.get_fileName_docID_dict()

def setup_processor():
	if "ABBYY_APPID" in os.environ:
		processor.ApplicationId = os.environ["ABBYY_APPID"]

	if "ABBYY_PWD" in os.environ:
		processor.Password = os.environ["ABBYY_PWD"]

	# Proxy settings
	if "http_proxy" in os.environ:
		proxy_string = os.environ["http_proxy"]
		print("Using http proxy at {}".format(proxy_string))
		processor.Proxies["http"] = proxy_string

	if "https_proxy" in os.environ:
		proxy_string = os.environ["https_proxy"]
		print("Using https proxy at {}".format(proxy_string))
		processor.Proxies["https"] = proxy_string

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/ocr/xml', methods=['POST'])
def ocr():
    global processor
    if request.method == 'POST':
        app.logger.info('Processing default request - pdf')
        if 'file' not in request.files:
            #flash('No file part')
            app.logger.info('No file part')  
            return ''
        file = request.files['file']
        app.logger.info(file.filename)
        if file and allowed_file(file.filename):
            
            # request???�일??upload ?�더???�?�하�?????file ?�용???�라�?
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

            # request�??�어??file??ocr 결과 xml??반환
            # 결과 xml?� UPLOAD_FOLDER???�?�됨
            ocrXml = api(processor, file, app.config['UPLOAD_FOLDER'])
            return ocrXml

# 중간 보고 데모 용
# def table_extractor_return(xml_path):

#     if xml_path =="/data1/saltlux/CJPoc/table-extraction/uploads/85.xml":
#         output_json = "85.json"
#     elif xml_path == "/data1/saltlux/CJPoc/table-extraction/uploads/86.xml":
#         output_json = "86.json"
#     elif xml_path == "/data1/saltlux/CJPoc/table-extraction/uploads/2017_S0899900717300047_Orange juice allied to a reduc.xml":
#         output_json = "2017_S0899900717300047_Orange juice allied to a reduc.pdf.json"
#     elif xml_path == "/data1/saltlux/CJPoc/table-extraction/uploads/2019_S096522991931115X_Clinical and psychological res.xml":
#         output_json = "2019_S096522991931115X_Clinical and psychological res.pdf.json"

#     print(output_json)

#     with open("/data1/saltlux/CJPoc/table-extraction/extractedTable/" + output_json) as json_file:
#         json_data = json.load(json_file)

#     return json.dumps(json_data, ensure_ascii=False, indent="\t")


@app.route('/extractedPreKB/regularizedValueWithHeader', methods=['POST'])
def get_regularized_value_with_header():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            print(request.data)
            value = json.loads(request.data)
            try:
                result = preKB_mapper.get_regularized_value_with_header(value)
                r = Response(response=json.dumps(result, indent=3), status=200, mimetype="application/json")
                return r
            except Exception as e:
                print("Value regularizing failed")
                print("Error: ", e)
                return "Value regularizing failed"


@app.route('/extractedPreKB/regularizedValue', methods=['POST'])
def get_regularized_value():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            print(request.data)
            value = json.loads(request.data)['input']
            try:
                result = preKB_mapper.get_regularized_value(value)
                r = Response(response=json.dumps(result, indent=3), status=200, mimetype="application/json")
                return r
            except Exception as e:
                print("Value regularizing failed")
                print("Error: ", e)
                return "Value regularizing failed"


@app.route('/extractedPreKB/semanticTag', methods=['POST'])
def semantic_tagging():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            print(request.data)
            headerList = json.loads(request.data)
            try:
                result = preKB_mapper.get_semantic_tag(headerList)
                r = Response(response=json.dumps(result, indent=3), status=200, mimetype="application/json")
                return r
            except Exception as e:
                print("Semantic tagging failed")
                print("Error: ", e)
                return "Semantic tagging failed"


@app.route('/extractedPreKB/HeaderValue', methods=['POST'])
def hv_extraction():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            xml_path = json.loads(request.data)['path']
            print(xml_path)   
              
            try:  
                extractedTables = xml_to_table(xml_path)["tableViewInfos"]
            except Exception as e:
                print("Header-Value extraction failed")
                print(xml_path)
                print("Error: ", e)
                return "Header-Value extraction failed"  
                
             
            try:
                hv_list = []  
                for i, extractedTable in enumerate(extractedTables):
                    caption = []
                    extractedTable['is_table'] = is_collect_table(extractedTable['table']) 
                    caption.extend(extractedTable['upcaption'])
                    caption.extend(extractedTable['downcaption'])
                    captions, row_header_list, col_header_list = get_header_value_info_new(extractedTable, caption)
                    table_type = get_type(captions, row_header_list, col_header_list)
                    extractedTable['table_type'] = table_type
                    hv_object = {"id": i, "table_type":extractedTable['table_type'], "hv":extractedTable["hv"]}
                    hv_list.append(hv_object)
                
                result = {"hvs": hv_list}
                r = Response(response=json.dumps(result, indent=3), status=200, mimetype="application/json")
                return r
            except Exception as e:
                print("table_type error")
                print(extractedTables)
                print("Error: ", e)
                return "table_type error"



        
@app.route('/extractedPreKB/fromTable', methods=['POST'])
def table_extraction():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            xml_path = json.loads(request.data)['path']
            print(xml_path)
            # 테이블 추출
            # ocrXml = request.data
            # rows = table_extractor_test.xml_to_list(ocrXml)
            # print(rows)
            try:
                result = preKB_mapper.PreKB(0, preKB_mapper.from_structured(xml_path)).toJson()
                r = Response(response=result, status=200, mimetype="application/json")
                return r
            except Exception as e:
                print("Table extraction failed")
                print("Error: ", e)
                return preKB_mapper.PreKB(1, []).toJson()

            return preKB_mapper.PreKB(1, []).toJson()


@app.route('/extractedPreKB/fromText', methods=['POST'])
def text_extraction():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            xml_path = json.loads(request.data)['path']
            print(xml_path)

            # DOC ID 확인
            try:
                doc_id = fileName_docID_dict[xml_path.split("/")[-1]]
            except Exception as e:
                print(xml_path.split("/")[-1])
                print("Couldn't find doc id from ", xml_path)
                print("Error: ")

                # Failed
                return preKB_mapper.PreKB(1, []).toJson()
            
            # extract preKB from text
            try:
                result = preKB_mapper.PreKB(0, preKB_mapper.from_unstructured(doc_id)).toJson()

                r = Response(response=result, status=200, mimetype="application/json")
                return r
            except Exception as e:
                print("Couldn't extract text from ", xml_path)
                print("Error: ", e)

                # Failed
                return preKB_mapper.PreKB(1, []).toJson()
            
            return preKB_mapper.PreKB(1, []).toJson()
    


@app.route('/extractedPreKB', methods=['POST'])
def preKB_extraction():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            print(request.data)
            xml_path = json.loads(request.data)['path']

            # DOC ID 확인
            try:
                doc_id = fileName_docID_dict[xml_path.split("/")[-1]]
            except Exception as e:
                print(xml_path.split("/")[-1])
                print("Couldn't find doc id from ", xml_path)
                print("Error: ", e)

                # Failed
                return preKB_mapper.PreKB(1, []).toJson()

            # extract preKB from table & text
            try:
                result = preKB_mapper.extract_preKB(xml_path, doc_id).toJson()
                r = Response(response=result, status=200, mimetype="application/json")
                return r
            except Exception as e:
                print("Couldn't extract preKB from ", xml_path)
                print("Error :", e)

                # Failed
                return preKB_mapper.PreKB(1, []).toJson()
            
            return preKB_mapper.PreKB(1, []).toJson()
        
        
@app.route('/extractedTableView', methods=['POST'])
def table_extraction2():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            pass
        else:
            xml_path = json.loads(request.data)['path']
            tables = table_view_extract.xml_to_list(xml_path)
            return json.dumps(tables, ensure_ascii=False, indent="\t")

if __name__ == "__main__":
    processor = AbbyyOnlineSdk()
    setup_processor()
    
    app.run(host='0.0.0.0', port=5555, threaded=True, debug=True)
