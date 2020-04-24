import os
import re
from bs4 import BeautifulSoup
from PorterStemmer import PorterStemmer
import hanlp
zh_tokenizer = hanlp.load('PKU_NAME_MERGED_SIX_MONTHS_CONVSEG')

def read_en_stopwords() -> list:
    ret = []
    with open("materials/en_stop_words.txt", "r") as f:
        ret = f.read().split("\n")
    return ret

def en_preprocess(file_path: str, stop_words: list, step: int = 4) -> str:
    '''
    Step1: Extract pure-text content from the original html file
    Step2: To lower case, remove special characters
    Step3: Remove stop words
    Step4: Porter stemming (Final result)
    '''
    with open(file_path, "r", encoding="UTF-8") as f:
        html_content = f.read()
        parsed_content = BeautifulSoup(html_content, 'html.parser')
        text_content = ""
        # Extract pure-text content from the original html file
        for child in parsed_content.find(id="mw-content-text").div.children:
            if child.name in ("p", "h2", "h3", "h4", "h5"):
                text_content += child.get_text()
        if step == 1:
            return text_content
        # To lower case
        text_content = text_content.lower()
        # Remove special characters
        text_content = text_content.replace("'", "")
        text_content = text_content.replace("-", "")
        for i in range(len(text_content)):
            curr_char = text_content[i]
            if not ((curr_char >= 'a' and curr_char <= 'z')):
                text_content = text_content.replace(curr_char, " ")
        # Remove duplicated spaces
        text_content = re.sub("[ ]+", " ", text_content)
        if step == 2:
            return text_content
        # Tokenize
        token_list = text_content.split(" ")
        # Remove stop words
        new_list = []
        for token in token_list:
            if token not in stop_words and token != "":
                new_list.append(token)
        token_list = new_list
        if step == 3:
            return text_content
        # Porter stemming
        p = PorterStemmer()
        new_list = []
        for i in range(len(token_list)):
            new_list.append(p.stem(token_list[i], 0, len(token_list[i]) - 1))
        token_list = new_list
        final_result = " ".join(token_list)
        return final_result

def read_zh_stopwords() -> list:
    ret = []
    with open("materials/zh_stop_words.txt", "r") as f:
        ret = f.read().split("\n")
    return ret

def zh_preprocess(file_path: str, stop_words: list, step: int = 3) -> str:
    '''
    Step1: Extract pure-text content from the original html file
    Step2: Tokenize
    Step3: Remove stop words and special characters (Final result)
    '''
    with open(file_path, "r", encoding="UTF-8") as f:
        html_content = f.read()
        parsed_content = BeautifulSoup(html_content, 'html.parser')
        text_content = ""
        # Extract pure-text content from the original html file
        text_content += "《" + parsed_content.findAll("h1")[0].string + "》"
        for child in parsed_content.find(id="paragraph").children:
            if child.name in ("p"):
                text_content += child.get_text()
        if step == 1:
            return text_content
        # Tokenize
        token_list = zh_tokenizer(text_content)
        if step == 2:
            return " ".join(token_list)
        # Remove stop words and special characters
        new_list = []
        for token in token_list:
            if token not in stop_words and token != "" and re.match("[^\u4e00-\u9fa5]", token) == None:
                new_list.append(token)
        token_list = new_list
        final_result = " ".join(token_list)
        return final_result

if __name__ == "__main__":
    fun = 2
    if fun == 1:
        path = "original_data/en_wiki/"
        stop_words = read_en_stopwords()
        file_list = os.listdir(path) #列出文件夹下所有的目录与文件
        for file_name in file_list:
            file_path = path + file_name
            if os.path.isfile(file_path):
                print("Processing " + file_path)
                result = en_preprocess(file_path, stop_words, 3)
                target_path = "processed_data/en_wiki_3/" + file_name
                print("Writing result to " + target_path)
                with open(target_path, "w", encoding="UTF-8") as f:
                    f.write(result)
    else:
        path = "original_data/zh_ithome/"
        stop_words = read_zh_stopwords()
        file_list = os.listdir(path) #列出文件夹下所有的目录与文件
        for file_name in file_list:
            file_path = path + file_name
            if os.path.isfile(file_path):
                print("Processing " + file_path)
                result = zh_preprocess(file_path, stop_words, 3)
                target_path = "processed_data/zh_ithome_final/" + file_name[:10] + ".txt"
                print("Writing result to " + target_path)
                with open(target_path, "w", encoding="UTF-8") as f:
                    f.write(result)