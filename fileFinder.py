import os



if __name__ == "__main__":
    import os
    print("hi")
    ###
    # wfile = "/data1/saltlux/CJPoc/table-extraction/xml_ch_78_names.txt" 
    # rfile = "/data1/saltlux/CJPoc/table-extraction/final_demo/task2_216/xml_cj_78"
    # list = os.listdir(rfile)
    # with open(wfile, "w", encoding="utf-8") as f:
    #     for i in range(len(list)):
    #         f.write(list[i])
    #         f.write("\n")
    ### 
    ###
    wfile = "/data1/saltlux/CJPoc/table-extraction/pdf_ch_78_names.txt" 
    rfile = "/data1/saltlux/CJPoc/table-extraction/final_demo/task2_216/papers_cj_78"
    list = os.listdir(rfile)
    with open(wfile, "w", encoding="utf-8") as f:
        for i in range(len(list)):
            f.write(list[i])
            f.write("\n")
    ###