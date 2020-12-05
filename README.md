### Abbyy-ocr-api
* 클라우드 기반 OCR 엔진 ABBYY를 편하게 사용할 수 있는 Flask 기반 API 서버
* API 형태로 파일을 업로드하거나 서버 내 파일 경로를 파라미터로 전달하면, xml 형태의 ocr 결과를 확인할 수 있음

### ABBYY Cloud 계정 연동
사용하기 위해서 ABBYY cloud 계정 정보를 환경 변수에 등록해주어야 함
* 계정 발급: https://cloud.ocrsdk.com/
* 환경 변수 등록
  * vi ~/.bahsrc
  * export ABBYY_APPID=''
  * export ABBYY_PWD=''


### 실행 방법
  * python ocr-flask.py

