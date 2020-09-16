from xml_to_table.table_extractor import xml_to_table
from table_classifier.tableClassifier import is_collect_table, get_type
from table_classifier.preprocessing import get_header_value_info_new
import os
import json

if __name__ == "__main__":

    BASE_DIR_PATH = "/data1/saltlux/CJPoc/table-extraction/final_demo/task1_30/task1_xml_30/"
    OUT_DIR_PATH = "/data1/saltlux/CJPoc/table-extraction/final_demo/task1_30/task1_table_result_30/"
    xml_list = os.listdir(BASE_DIR_PATH)
    
    for xml_path in xml_list:
        print(xml_path)
        tables = xml_to_table(BASE_DIR_PATH + xml_path)

        result = {
            "tableViewInfos" : []
        }

        for table in tables['tableViewInfos']:
            caption = []
            is_table = is_collect_table(table['table']) 
            table['is_table'] = is_table
            caption.extend(table['upcaption'])
            caption.extend(table['downcaption'])
            captions, row_header_list, col_header_list = get_header_value_info_new(table, caption)
            table_type = get_type(captions, row_header_list, col_header_list)
            table['table_type'] = table_type
            
            result["tableViewInfos"].append(
                    {
                        "table": table['table'],
                        #"table_html": None,
                        #"table_html": refine_html(pd.DataFrame(text_table).to_html()),
                        "axis" : table['axis'],
                        "page" : table['page'],
                        "hv": table['hv'],
                        "is_table": is_table,
                        "table_type": table_type
                    }
                )   
        result = json.dumps(result, indent = 3)
        with open(OUT_DIR_PATH + "hv_" + xml_path.split(".")[0] + ".json", 'w') as outFile:
            outFile.write(result)