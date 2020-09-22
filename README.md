# CJ poc 지식 추출기

## 지식 추출기 API 서버 실행 방법
```bash
conda activate table # conda "table" 가상 환경 사용
cd /data1/saltlux/CJPoc/table-extraction/
nohup python te-flask.py > log_flask/log_20200922.out & # 적절한 로그 파일 이름 사용
```

## 프로젝트 구조
### OCR 모듈
* abbyy
### Table 추출 모듈
* table_classifier
* table_semantic_tagging
* xml_to_table
* preKB_mapper.py
### API server
* te-flask.py
### Data folder
* demo
* final_demo
* ocr-output
* cj-poc-papers
### log
* ./log_flask

