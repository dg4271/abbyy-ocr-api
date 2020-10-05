import os

class Node:
    def __init__(self, key, data=None):
        self.key = key
        self.data = data
        self.children = {}
        
class Trie:
    def __init__(self):
        self.head = Node(None)
    
    """
    Insert string into Trie.
    save a string at last node.
    """
    def insert(self, string):
        curr_node = self.head
        
        for char in string:
            if char not in curr_node.children:
                curr_node.children[char] = Node(char)
            
            curr_node = curr_node.children[char]
            
        curr_node.data = string
    
    """
    Search String from Trie.(T/F)
    """
    def search(self, string):
        curr_node = self.head        
        
        for char in string:
            if char in curr_node.children:
                curr_node = curr_node.children[char] 
            else:
                return False
            
        if (curr_node.data != None):
            return True
        
        return False
    
    """
    Search data from Trie
    """
    def searchData(self, string):
        curr_node = self.head
        
        for char in string:
            if char in curr_node.children:
                curr_node = curr_node.children[char]
            else:
                return False
        
        if (curr_node.data != None):
            return curr_node.data
        
        return False

    """
    Insert data into Trie as label
    """
    def insertLabeled(self, string, label):
        curr_node = self.head
        
        for char in string:
            if char not in curr_node.children:
                curr_node.children[char] = Node(char)    
            curr_node = curr_node.children[char]
        
        curr_node.data = label

class customTrie:
    def __init__(self):
        self.file_path = ""
    
    def setPath(self, file_path):
        if os.path.isfile(file_path):
            self.file_path = file_path
            return True
        else:
            return False
    
    def getPath(self):
        return self.file_path
            
    def retrieveDictionary(self, file_path = ""):
        if file_path != "":
            self.file_path  = file_path

        trie = Trie()
        with open(self.file_path,"r",encoding="utf-8") as f:
            for line in f:
                line = line.replace("\n","")
                line_split = line.split("\t")
                
                label =  line_split[0]
                
                if len(line_split) > 1:
                    for string in line_split[1].split(","):
                        trie.insertLabeled( string, label )
                        
                elif len(line_split) == 1:
                    trie.insert(label)
                    
                else:
                    continue
        return trie
