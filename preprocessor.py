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

def en_preprocess(file_path: str, stop_words) -> str:
    with open(file_path, "r", encoding="UTF-8") as f:
        html_content = f.read()
        parsed_content = BeautifulSoup(html_content, 'html.parser')
        text_content = ""
        # Extract pure-text content from the original html file
        for child in parsed_content.find(id="mw-content-text").div.children:
            if child.name in ("p", "h2", "h3", "h4", "h5"):
                text_content += child.get_text()
        # To lower case
        text_content = text_content.lower()
        # Remove special characters
        text_content = text_content.replace("'", "")
        text_content = text_content.replace("-", "")
        for i in range(len(text_content)):
            curr_char = text_content[i]
            if not ((curr_char >= 'a' and curr_char <= 'z')): # or (curr_char >= '0' and curr_char <= '9')):
                text_content = text_content.replace(curr_char, " ")
        # Remove duplicated spaces
        text_content = re.sub("[ ]+", " ", text_content)
        # Tokenize
        token_list = text_content.split(" ")
        # Remove stop words
        new_list = []
        for token in token_list:
            if token not in stop_words and token != "":
                new_list.append(token)
        token_list = new_list
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

def zh_preprocess(file_path: str, stop_words: list, step: int = 2) -> str:
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
        # Remove special characters
        text_content = re.sub("[^\u4e00-\u9fa5]", " ", text_content)
        # Tokenize
        token_list = zh_tokenizer(text_content)
        # Remove stop words
        new_list = []
        for token in token_list:
            if token not in stop_words and token != "":
                new_list.append(token)
        token_list = new_list
        final_result = " ".join(token_list)
        final_result = re.sub("[ ]+", " ", final_result)
        return final_result

if __name__ == "__main__":
    # path = "original_data/en_wiki/"
    # stop_words = read_en_stopwords()
    # file_list = os.listdir(path) #列出文件夹下所有的目录与文件
    # for file_name in file_list:
    #     file_path = path + file_name
    #     if os.path.isfile(file_path):
    #         print("Processing " + file_path)
    #         result = en_preprocess(file_path, stop_words)
    #         target_path = "processed_data/en_wiki/" + file_name
    #         print("Writing result to " + target_path)
    #         with open(target_path, "w", encoding="UTF-8") as f:
    #             f.write(result)

    path = "original_data/zh_ithome/"
    stop_words = read_zh_stopwords()
    file_list = os.listdir(path) #列出文件夹下所有的目录与文件
    for file_name in file_list:
        file_path = path + file_name
        if os.path.isfile(file_path):
            print("Processing " + file_path)
            result = zh_preprocess(file_path, stop_words, 1)
            target_path = "processed_data/main_body/zh_ithome/" + file_name[:10] + ".txt"
            print("Writing result to " + target_path)
            with open(target_path, "w", encoding="UTF-8") as f:
                f.write(result)