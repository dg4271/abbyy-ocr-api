# -*- coding: utf-8 -*- 

from flask import Flask, request, jsonify, Response
import logging
import json

from abbyy.AbbyyOnlineSdk import AbbyyOnlineSdk
from abbyy.ocrProcess import *

# Flask
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
logging.basicConfig(level = logging.INFO)

# Abbyy
processor = None

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
def ocr_xml():
    global processor
    if request.method == 'POST':
        app.logger.info('Processing default request - pdf')

        # ocr using uploaded file
        print(request.files)
        if request.data and 'file' in json.loads(request.data).keys():
            file_path = json.loads(request.data)['file']
            result = {}
            try:
                with open(file_path, 'rb') as pdf_file:
                    api(processor, pdf_file, file_path.split('/')[-1], app.config['UPLOAD_FOLDER'])
                
                result['result_code'] = 1
                result['result_xml_path'] = app.config['UPLOAD_FOLDER']
            except:
                result['result_code'] = 0
                result['result_xml_path'] = ""

            r = Response(response=json.dumps(result, indent=3), status=200, mimetype="application/json")
            return r

        else:
            app.logger.info('No file part')
            r = Response(response=json.dumps({'result_code':0, 'result_xml_path':""}, indent=3), status=200, mimetype="application/json")
            return r

@app.route('/ocr/xml/string', methods=['POST'])
def ocr_xml_string():
    global processor
    if request.method == 'POST':
        app.logger.info('Processing default request - pdf')

        # ocr using uploaded file
        print(request.files)
        if request.files:
            file = request.files['file']
            app.logger.info(file.filename)
            if file and allowed_file(file.filename):
                ocrXml = api(processor, file, file.filename, app.config['UPLOAD_FOLDER'])
                return ocrXml
        else:
            app.logger.info('No file part')
            r = Response(response=json.dumps({'result_code':0, 'result_xml_path':""}, indent=3), status=200, mimetype="application/json")
            return r   


if __name__ == "__main__":
    processor = AbbyyOnlineSdk()
    setup_processor()
    
    app.run(host='0.0.0.0', port=7777, threaded=True)
