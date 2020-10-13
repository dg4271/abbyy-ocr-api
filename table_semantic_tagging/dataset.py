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
    import trie
    import os
    print("hi")
    customTrie = trie.customTrie()
    path = os.path.dirname(os.path.abspath(__file__)) + "/dic/" + "dicUnit.txt"
    print(customTrie.setPath(path))
    unitDic = customTrie.retrieveDictionary(path)
    print(unitDic.searchData("miligram"))
    print(customTrie.getPath())
    print("bye")
    