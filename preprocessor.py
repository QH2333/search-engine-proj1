import os
import time
import re
import urllib.parse
from bs4 import BeautifulSoup
from PorterStemmer import PorterStemmer
import crawler
import jieba
# import hanlp
# zh_tokenizer = hanlp.load('PKU_NAME_MERGED_SIX_MONTHS_CONVSEG')

doc_count = 0

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
            return " ".join(token_list)
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
        token_list = jieba.cut_for_search(text_content)
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

def download_and_preprocess(URL: str, file_name: str, category: str, process_fun, stop_words: list, use_system: bool = True) -> bool:
    if crawler.save_html(URL, file_name + "_org.txt", category, False) == True:
        file_path = "original_data/" + category + "/" + file_name + "_org.txt"
        result = process_fun(file_path, stop_words)
        target_path = "processed_data/" + category + "_final/" + file_name + ".txt"
        print("Writing result to " + target_path)
        with open(target_path, "w", encoding="UTF-8") as f:
            f.write(result)
        return True
    else:
        return False

def crawl_and_preprocess(seed_URL: str, name_fun, pattern: str, max_count: int, category: str, process_fun, stop_words: list, use_system: bool = True, cooling_down: float = 0):
    global doc_count
    URL_queue = [seed_URL]
    processed_queue = []
    while len(URL_queue) != 0 and doc_count < max_count:
        this_URL = URL_queue[0]
        URL_queue = URL_queue[1:]
        processed_queue.append(this_URL)
        if download_and_preprocess(this_URL, name_fun(this_URL), category, process_fun, stop_words, use_system) == True:
            # Parse the page for new links, if it was successfully preprocessed
            file_path = "original_data/" + category + "/" + name_fun(this_URL) + "_org.txt"
            with open(file_path, "r", encoding="UTF-8") as f:
                html_content = f.read()
                parsed_content = BeautifulSoup(html_content, 'html.parser')
                for link in parsed_content.findAll("a"):
                    href = link.get("href")
                    if href:
                        if "#" in href:
                            href = href[:href.find("#")]
                        href = urllib.parse.urljoin(this_URL, href)
                        if (re.match(pattern, href)) and (href not in processed_queue):
                            URL_queue.append(href)
            doc_count += 1
        time.sleep(cooling_down)

def zh_naming(URL: str) -> str:
    article_id = re.findall("\d\d\d", URL)
    return "zh_%s_%s" % (article_id[0], article_id[1])

if __name__ == "__main__":
    zh_stopwords = read_zh_stopwords()
    en_stopwords = read_en_stopwords()

    # # Preprocess only
    # path = "original_data/en_wiki/"
    # file_list = os.listdir(path) #列出文件夹下所有的目录与文件
    # for file_name in file_list:
    #     file_path = path + file_name
    #     if os.path.isfile(file_path):
    #         print("Processing " + file_path)
    #         result = en_preprocess(file_path, en_stopwords, 3)
    #         target_path = "processed_data/en_wiki_3/" + file_name
    #         print("Writing result to " + target_path)
    #         with open(target_path, "w", encoding="UTF-8") as f:
    #             f.write(result)

    # path = "original_data/zh_ithome/"
    # file_list = os.listdir(path) #列出文件夹下所有的目录与文件
    # for file_name in file_list:
    #     file_path = path + file_name
    #     if os.path.isfile(file_path):
    #         print("Processing " + file_path)
    #         result = zh_preprocess(file_path, zh_stopwords, 1)
    #         target_path = "processed_data/zh_ithome_1/" + file_name[:10] + ".txt"
    #         print("Writing result to " + target_path)
    #         with open(target_path, "w", encoding="UTF-8") as f:
    #             f.write(result)

    # ############################################################################

    # # Chinese: IT Home
    # for i in range(483, 484):
    #     for j in range(226, 1000):
    #         URL = "https://www.ithome.com/0/%d/%d.htm" % (i, j)
    #         file_name = "zh_%d_%d" % (i, j)
    #         category = "zh_ithome"
    #         download_and_preprocess(URL, file_name, category, zh_preprocess, zh_stopwords, False)
    #         time.sleep(0.1) # Avoid overloading the server

    # # English: Wikipedia
    # with open("original_data/wiki_article_list.txt", "r") as f:
    #     for line in f.readlines():
    #         article_name = line[:-1]
    #         URL = "https://en.wikipedia.org/wiki/" + article_name
    #         file_name = article_name
    #         if file_name.find(":") != -1:
    #             file_name = file_name.replace(":", "_", -1)
    #         category = "en_wiki"
    #         download_and_preprocess(URL, file_name, category, en_preprocess, en_stopwords, True)

    # ############################################################################

    crawl_and_preprocess(seed_URL="https://www.ithome.com/0/484/486.htm",
        # name_fun=(lambda URL: "ZH_" + str(doc_count)), 
        name_fun=zh_naming, 
        pattern="https://www.ithome.com/0/\\d\\d\\d/\\d\\d\\d.htm",
        max_count=100,
        category="zh_crawler",
        process_fun=zh_preprocess,
        stop_words=zh_stopwords,
        use_system=False,
        cooling_down=0.1,
    )

    # crawl_and_preprocess(seed_URL="https://en.wikipedia.org/wiki/Main_Page",
    #     # name_fun=(lambda URL: "EN_" + str(doc_count)), 
    #     name_fun=(lambda URL: URL[30:].replace(":", "_", -1)), 
    #     pattern="https://en.wikipedia.org/wiki/.*",
    #     max_count=1000,
    #     category="en_crawler",
    #     process_fun=en_preprocess,
    #     stop_words=en_stopwords,
    #     use_system=True,
    #     cooling_down=0,
    # )