# 搜索引擎项目一：文本预处理

## 概述

这是2020年SWJTU搜索引擎课程的第一个项目，项目的主要功能是**爬取足够数量的网页并对其进行预处理**，以便后续对其进行索引。

我的代码基于Python实现，代码里使用了这些第三方模块：

- bs4
- hanlp

另外还引用了位于[这里](https://tartarus.org/martin/PorterStemmer/python.txt)的Porter Stemming算法Python实现。

## 实现过程

### 网页下载器/爬虫

这部分的代码实现位于`crawler.py`文件中，对国内知名媒体**IT之家**和英文**维基百科**两个站点上的文档自动进行批量下载。

#### save_html()

下载并保存单个网页是通过`save_html()`函数实现的，这个函数提供了两种不同的下载方法：使用使用`get_html()`下载函数（下面详细描述），或者系统自带模块`urllib.request`。使用时向`save_html()`函数传递网页的URL、保存的文件名和类别，然后函数就会自动按类别创建文件夹，然后将URL指向的网页按指定的文件名保存到这个文件夹里。

#### get_html()

`get_html()`函数是一个使用套接字编程实现的网页下载函数。传入网页URL后，首先判断URL格式是否合法，如果合法就接着判断URL采用的是`HTTP`协议还是`HTTPS`协议，然后对应地，分别创建普通套接字和带SSL包装的套接字，最后调用`get_response_body()`获取网页内容，如果成功获取到网页内容就以字符串形式返回网页的内容，否则抛出错误。

#### get_response_body()

这是一个用于获取HTTP响应正文的函数，函数声明如下：

```Python
def get_response_body(sock, host: str, path: str, verbose: bool = True) -> str:
```

设计上，该函数遵从`HTTP1.1`协议（不支持`HTTP2.0/HTTP3.0`），当接收到URL参数后，函数构造一个最小的`HTTP1.1 GET`请求报文，请求头部仅包含`Host`信息，例如：

``` HTTP
GET / HTTP/1.1
Host: www.baidu.com
```

然后，通过参数中传入的套接字连接到目标主机，发送HTTP请求报文，并等待目标主机的回复。这部分对应的代码是：

```Python
    # Make an HTTP request
    request = "GET %s HTTP/1.1\r\n" % (path)
    request += "Host: %s\r\n" % (host)
    request += "\r\n"
    sock.send(request.encode("UTF-8"))
```

正常情况下，目标主机通过套接字返回的HTTP响应报文包括状态行、响应头、响应正文三部分，一个充分实现了HTTP协议的解析程序需要能够识别这三部分内包括的所有信息。由于本函数的目的只是下载**响应正文**中的数据，所以并没有充分实现HTTP协议，而是做了大幅简化。

要下载响应正文，首先需要知道响应正文的长度，这一数据包括在响应头的`Content-length`字段中，于是思路便是：从套接字中读取数据，直到响应头完全被接收，然后解析得到响应头中的`Content-length`字段值，读取对应长度的响应正文数据。根据协议格式，响应头和响应正文间用一个空行`\r\n`隔开，加上响应头最后的一个`\r\n`，当套接字中接收到连续的`\r\n\r\n`四个字符就可以判定响应头（包括状态行）已经完全被接收，至此为第一步。第二步使用正则表达式匹配状态行信息，获取HTTP响应状态，如果遇到非正常情况（状态码不是200），则直接抛出错误，否则继续。第三步再次使用正则表达式匹配`Content-length`字段，就可以获取到响应正文的长度。

获取到正文长度信息后，只需要循环读取套接字中收到的数据，直至正文接收完毕，就可以以字符串形式返回正文数据。

```Python
    response = b""
    while response.find(b"\r\n\r\n") == -1: # Still receiving header
        data = sock.recv(1024)
        response += data
    content_pos = response.find(b"\r\n\r\n") + 4 # Where the content begins
    header = response[0:content_pos - 4].decode("UTF-8") # Get header
    content = response[content_pos:] # Get received content

    find_status = re.search('^HTTP/1.1 [0-9][0-9][0-9]', header)
    if not find_status:
        raise Exception("Invalid response")
    if find_status.group()[-3:] != "200":
        raise Exception("Incorrect status" + find_status.group()[-3:])

    find_length = re.search("Content-Length: [0-9]*", header)
    if not find_length:
        raise Exception("Unknown content length")
    content_length = int(find_length.group()[16:])
    while content_length > len(content):
        data = sock.recv(min(1024, content_length - len(content)))
        content += data
    content = content.decode("UTF-8")
    return content
```

由于本函数只实现了对`HTTP1.1`的支持，可能无法下载部分站点上的文档，所以`save_html()`函数中还提供了基于`urllib.request`系统模块的下载选项。

#### 爬取网页并保存

实现了网页下载功能后，爬虫就比较简单了。对目标站点的URL格式进行研究可以发现，IT之家的文章URL格式可以用`https://www.ithome.com/0/<i>/<j>.htm`描述，其中`j`的取值范围是`100-999`，溢出后向`i`进一，2020年4月15日`i`已经增长至`482`。这里编写程序读取`481-482`这一范围内的`i`对应的文章，共爬取到`1216`篇有效文档。

维基百科的文章URL格式可以用`https://en.wikipedia.org/wiki/<article_name>`描述，由于文章名称没有规律，所以需要预先获取一份文章名称列表。这里使用了维基百科用户West.andrew.g提供的一份最流行的5000个维基百科页面的[列表](https://en.wikipedia.org/wiki/User:West.andrew.g/Popular_pages)，使用`JavaScrip`简单处理以后将其保存为txt文件以供程序自动爬取：

```JavaScript
var lines = document.getElementById("interest").getElementsByTagName("tbody")[0].getElementsByTagName("tr");
var text = "";
for (elem of lines) {
    text = text.concat(elem.getElementsByTagName("td")[1].getElementsByTagName("a")[0].getAttribute("href"));
    text = text.concat(",");
}
console.log(text);
```

这里共下载了`1081`篇有效的维基百科文档。

### 预处理

预处理模块对英文文档进行了如下操作：

- S1:提取正文内容
- S2:将各个单词进行字符化：删除特殊字符、所有字符转换为小写
- S3:删除英文停用词
- S4:调用英文Porter Stemming功能
- 经过以上处理之后，将经过处理之后所形成简化文档保存（如：News_1_E.txt），以备以后的索引处理

对中文文档进行了如下操作：

- S1:提取正文内容
- S2:将中文文档进行字符化：调研并选择合适的中文分词技术和工具实现中文分词
- S3:删除中文停用词和带特殊字符的Token
- 经过以上处理之后，将经过处理之后所形成简化文档保存（如：News_1_C.txt），以备以后的索引处理

这部分的代码实现位于`preprocessor.py`文件中

#### 对英文文档的处理

这里使用了一个函数`en_preprocess()`来打包整个对英文文档的处理过程，函数接收一个字符串类型的原始文档路径参数和预先读取的停用词列表（后续介绍），然后以字符串形式返回处理结果。

```Python
def en_preprocess(file_path: str, stop_words: list, step: int = 4) -> str:
    '''
    Step1: Extract pure-text content from the original html file
    Step2: To lower case, remove special characters
    Step3: Remove stop words
    Step4: Porter stemming (Final result)
    '''
```

对于每一个HTML文档，我们首先将其所有内容读入程序，这里使用Python的with语法结构，可以保证文件的正确关闭：

```Python
with open(file_path, "r", encoding="UTF-8") as f:
    html_content = f.read()
    ...
```

##### 提取英文正文内容

网页的源代码中存在大量HTML标签、CSS代码、JavaScript代码和标注信息，这些内容都会干扰搜索引擎的索引，所以要在预处理过程中去除。去除后，这里只保留文章正文的内容。由于不同站点页面的格式不同，提取正文的程序需要针对特定站点编写。

提取网页正文的第一步是解析网页的HTML源文件，这一工作通过`Beautiful Soup`模块实现。`Beautiful Soup`是一个功能强大的模块，主要功能是从网页抓取数据，它提供了一些简单的函数来解析HTML文档，并为用户提供需要抓取的数据。这里首先利用之前读取的文档内容构造一个`BeautifulSoup`类的实例，以备后续处理。

```Python
    parsed_content = BeautifulSoup(html_content, 'html.parser')
```

通过查阅浏览器的开发者模式发现，一篇维基百科文档的正文部分位于`id`属性为`mw-content-text`的`div`标签内部，正文段落和标题分别用`p`和`h2`等标签包裹。这里直接用`Beautiful Soup`提供的`find()`函数找到正文所在的`div`标签，遍历其内部所有标签，一旦发现正文段落或标题就将其内容追加到`text_content`后。经过验证，这样可以准确地提取正文内容。

```Python
    text_content = ""
    # Extract pure-text content from the original html file
    for child in parsed_content.find(id="mw-content-text").div.children:
        if child.name in ("p", "h2", "h3", "h4", "h5"):
            text_content += child.get_text()
```

##### 大小写转换、删除特殊字符

首先进行进行大小写转换的工作。由于上一步已经将网页正文内容解析为字符串格式，这一步直接调用Python内置字符串函数`lower()`即可。

```Python
    # To lower case
    text_content = text_content.lower()
```

第二步删除特殊字符。这里将正文字符串中所有不属于小写英文字母（由于已经经过大小写转换，不可能出现大写字符）和数字的字符都作为特殊字符，用空格代替。注意，这里对撇、连词符做了特殊处理，认为其两侧的字符属于同一个单词，所以直接将其删去而不是替换为空格。然后，为了避免多个连续空格影响后续Tokenize步骤，使用正则表达式匹配所有连续的多个空格，将其全都替换为一个空格。

```Python
    # Remove special characters
    text_content = text_content.replace("'", "")
    text_content = text_content.replace("-", "")
    for i in range(len(text_content)):
        curr_char = text_content[i]
        if not ((curr_char >= 'a' and curr_char <= 'z')):
            text_content = text_content.replace(curr_char, " ")
    # Remove duplicated spaces
    text_content = re.sub("[ ]+", " ", text_content)
```

##### 移除英文停用词

为了方便这一步的处理，我们把删去特殊字符的正文内容切分为单词列表形式，具体实现只需要直接调用Python内置字符串处理函数`split()`即可。该函数接收一个字符串参数作为分隔符，然后对指定字符串进行切片，以字符串列表的形式返回切片的结果。经过之前的预处理步骤处理后的正文字符串只包含用空格分隔的英文单词，所以用空格为参数调用`split()`函数。

```Python
    # Tokenize
    token_list = text_content.split(" ")
```

移除停用词之前，首先要读入停用词清单，将其放置在列表中以备使用。这里定义了一个函数来处理这项工作。

```Python
def read_en_stopwords() -> list:
    ret = []
    with open("materials/en_stop_words.txt", "r") as f:
        ret = f.read().split("\n")
    return ret
```

调用以上函数并将停用词列表保存在`stop_words`变量中，然后就可以进行停用词移除处理。首先遍历`token_list`中的每一个单词，然后逐一判断单词是否属于停用词，如果不属于停用词就把这个单词放到临时列表`new_list`中。当所有单词都处理完毕时，`new_list`中保存的就是移除了停用词的正文单词列表，只需要将其赋值给`token_list`即可。

```Python
    # Remove stop words
    new_list = []
    for token in token_list:
        if token not in stop_words and token != "":
            new_list.append(token)
    token_list = new_list
```

##### Porter Stemming

这里调用官方的Python版Porter Stemmer来实现提取词干，出处在[这里](https://tartarus.org/martin/PorterStemmer/python.txt)。使用上，需要先创建一个`PorterStemmer`类的实例`p`，然后在`p`上调用函数`stem()`，传入字符串类型的单词、整数类型的单词起止下标，函数就会返回词干提取的结果。这一部分的代码的框架与“移除停用词”部分基本类似，遍历处理`token_list`，然后将结果放入临时列表`new_list`，最后把临时列表赋值给`token_list`。

```Python
    # Porter stemming
    p = PorterStemmer()
    new_list = []
    for i in range(len(token_list)):
        new_list.append(p.stem(token_list[i], 0, len(token_list[i]) - 1))
    token_list = new_list
```

这时候`token_list`中保存的就是列表形式的最终结果，为了方便后续将其保存为文本文件，我们使用`join()`函数将其转换成字符串，然后返回。

```Python
    final_result = " ".join(token_list)
    return final_result
```

至此，英文文档的处理工作已经完成，只需要将结果保存为文件即可。

#### 对中文文档的处理

中文文档的处理函数框架与英文文档处理函数相同，首先定义一个函数来打包整个处理过程，然后在其中打开原始HTML文档并读取所有内容。

```Python
def zh_preprocess(file_path: str, stop_words: list, step: int = 3) -> str:
    '''
    Step1: Extract pure-text content from the original html file
    Step2: Tokenize
    Step3: Remove stop words and special characters (Final result)
    '''
    with open(file_path, "r", encoding="UTF-8") as f:
        html_content = f.read()
        ...
```

##### 提取中文正文内容

对中文文档正文的提取同样使用`Beautiful Soup`模块。一篇IT之家文章的标题位于文档中唯一的`h1`标签内部，正文部分位于`id`属性为`paragraph`的`div`标签内部，正文的每一个段落都用`p`标签包裹。与英文文档正文的提取相同，这里使用`find()`函数找到正文所在的`div`标签，遍历其内部所有标签，将所有正文段落的内容追加到`text_content`后。

```Python
    parsed_content = BeautifulSoup(html_content, 'html.parser')
    text_content = ""
    # Extract pure-text content from the original html file
    text_content += "《" + parsed_content.findAll("h1")[0].string + "》"
    for child in parsed_content.find(id="paragraph").children:
        if child.name in ("p"):
            text_content += child.get_text()
```

##### 对中文分词技术的调研

经过调研得知，常用中文分词框架包括jieba、HanLP、pkuseg、THULAC、NLPIR等。其中，jieba、HanLP是开源框架，pkuseg、THULAC、NLPIR分别是北京大学、清华大学、中科院计算所提供的NLP处理框架。

从使用便捷程度上说，四个库都支持Python，并且都可以通过pip快速下载使用，没有太大区别。从社区角度上说，jieba、HanLP两个框架较为活跃，pkuseg活跃度一般，而THULAC框架从2018年以后没有更新。从准确度上讲，。其他特点上，根据HanLP官方的说明，其训练的语料比较多，载入了很多实体库，在实体边界的识别上有一定的优势，可以更好地识别一些专有名词。

##### 实现中文分词

经过上一节的对比分析，这里决定使用hanlp这一中文分词器，在Python中使用这一分词器只需要安装并导入`hanlp`模块即可。使用hanlp的第一步是加载预训练模型，根据官方示例，这里加载一个名为`PKU_NAME_MERGED_SIX_MONTHS_CONVSEG`的分词模型。下面的两行代码位于代码文件的开头部分、所有函数外部。

```Python
import hanlp
zh_tokenizer = hanlp.load('PKU_NAME_MERGED_SIX_MONTHS_CONVSEG')
```

模型加载完成后返回一个函数对象，将其保存在变量`zh_tokenizer`中，然后就可以像正常函数那样调用这个函数变量。回到中文文档处理函数中，只需要向`zh_tokenizer`传入正文字符串即可一步完成分词，返回值是一个单词列表，将其保存在变量`token_list`中。

```Python
    # Tokenize
    token_list = zh_tokenizer(text_content)
```

##### 移除中文停用词和特殊字符

移除中文停用词的步骤与移除英文停用词的步骤基本相同，首先调用以下函数读取中文停用词列表并将这一列表保存在`stop_words`变量中。

```Python
def read_zh_stopwords() -> list:
    ret = []
    with open("materials/zh_stop_words.txt", "r") as f:
        ret = f.read().split("\n")
    return ret
```

然后遍历单词列表`token_list`，删除所有出现在停用词表中的单词就完成了“移除中文停用词”这一步骤。因为这里处理的是中文文档，所以我们认为非中文的字符（包括英文字母、数字、标点符号等）都属于特殊字符，使用`[^\u4e00-\u9fa5]`这一正则表达式来匹配，一旦某个Token中包含特殊字符，就将其删去。

```Python
    # Remove stop words
    new_list = []
    for token in token_list:
        if token not in stop_words and token != "" and re.match("[^\u4e00-\u9fa5]", token) == None:
            new_list.append(token)
    token_list = new_list
```

最后将保存最终结果的列表转换为字符串，并返回。

```Python
    final_result = " ".join(token_list)
    return final_result
```
