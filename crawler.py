import os
import time
import socket
import ssl
import urllib.request
import urllib.parse
import re

def get_response_body(sock, host: str, path: str, verbose: bool = True) -> str:
    request = "GET %s HTTP/1.1\r\n" % (path)
    request += "Host: %s\r\n" % (host)
    request += "\r\n"
    if verbose:
        print("Sending request:")
        print(request)
    sock.send(request.encode("UTF-8"))
    
    response = b""
    while response.find(b"\r\n\r\n") == -1: # Still receiving header
        data = sock.recv(1024)
        response += data
    content_pos = response.find(b"\r\n\r\n") + 4 # Where the content begins
    header = response[0:content_pos - 4].decode("UTF-8")
    content = response[content_pos:]
    if verbose:
        print("Got response header:")
        header = header.replace("\r\n", " ", -1)
        print(header)
    
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
    if verbose:
        print("Got response body:")
        print(content)
    return content

def get_html(URL: str, verbose: bool = True) -> str:
    if not re.match('^(https|http)://.+$', URL): # Invalid URL
        raise Exception("Invalid URL")
    parse_result = urllib.parse.urlparse(URL)

    content = ""
    if (parse_result.scheme.lower() == "https"): # Using sslsocket
        context = ssl.create_default_context()
        with socket.create_connection((parse_result.netloc, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=parse_result.netloc) as ssock:
                if parse_result.query != '':
                    content = get_response_body(ssock, parse_result.netloc, parse_result.path + "?" + parse_result.query, verbose)
                content = get_response_body(ssock, parse_result.netloc, parse_result.path, verbose)
                    
    if (parse_result.scheme.lower() == "http"): # Using normal socket
        context = ssl.create_default_context()
        with socket.create_connection((parse_result.netloc, 80)) as sock:
            if parse_result.query != '':
                content = get_response_body(sock, parse_result.netloc, parse_result.path + "?" + parse_result.query, verbose)
            content = get_response_body(sock, parse_result.netloc, parse_result.path, verbose)
    
    return content

def save_html(URL: str, file_name: str, category: str, use_system: bool = True):
    try:
        content = ""
        if use_system == True:
            resp = urllib.request.urlopen(URL)
            if resp.status != 200:
                raise Exception("Incorrect status")
            content = resp.read().decode("UTF-8")
        else:
            content = get_html(URL, verbose=False) # Support HTTP1.1
        with open("original_data/%s/%s" % (category, file_name), "w", encoding="UTF-8") as f:
            f.write(content)
        print("Successfully saved " + URL)
    except Exception as e:
        print("Failed to request " + URL)

if __name__ == "__main__":
    # # Chinese: IT之家 
    # for i in range(481, 482):
    #     for j in range(100, 1000):
    #         save_html("https://www.ithome.com/0/%d/%d.htm" % (i, j), "zh_%d_%d_org.txt" % (i, j), "zh_ithome")
    #         time.sleep(1)

    # English: Wikipedia
    with open("data/wiki_article_list.txt", "r") as f:
        for line in f.readlines():
            # Bug: This will delete the last char of last line
            article_name = line[:-1]
            file_name = article_name
            if file_name.find(":") != -1:
                file_name = file_name.replace(":", "_", -1)
            save_html("https://en.wikipedia.org/wiki/" + article_name, file_name + ".txt", "en_wiki")