import os

dicPath = os.path.dirname(os.path.abspath(__file__)) + "/dic/"   
dicAttribute = "dicAttribute.txt"
dicHeader = "dicHeader.txt"
dicUnit = "dicUnit.txt"

def add_item( dic_name, dic_key, dic_value):
    with open(dicPath + dic_name, "w", encoding="utf-8") as f:
        f.write( dic_key + "\t" + dic_value.replace(", ",",") + "\n")
        f.flush()


if __name__ == "__main__":
    # add_item( "hi.txt", "hello", "python")
    print("hi")