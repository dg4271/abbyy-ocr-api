from xml_to_table.table_extractor import xml_to_table
from table_classifier.tableClassifier import is_collect_table, get_type
from table_classifier.preprocessing import get_header_value_info_new

if __name__ =='__main__':
  test_xml = '/data1/saltlux/CJPoc/table-extraction/final_demo/task1_30/task1_xml_30/2019_S259011251930009X_Nutritional ketosis for mild c.xml'
  tables = xml_to_table(test_xml)

  for table in tables['tableViewInfos']:
    caption = []
    is_table = is_collect_table(table['table']) 
    table['is_table'] = is_table
    caption.extend(table['upcaption'])
    caption.extend(table['downcaption'])
    captions, row_header_list, col_header_list = get_header_value_info_new(table, caption)
    table_type = get_type(captions, row_header_list, col_header_list)
    table['table_type'] = table_type

  print(tables)





  