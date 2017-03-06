from bs4 import BeautifulSoup
import requests
import urllib.request
from html.parser import HTMLParser
from re import sub
import json


class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + ' ')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.__text.append('\n')

    def handle_endtag(self, tag):
        if tag == 'span':
            len_text = len(self.__text)
            word = str(self.__text[len_text - 1])
            word = word.rstrip()
            self.__text[len_text - 1] = word

    def text(self):
        return ''.join(self.__text)

    def get_poem_text(text):
        parser = MyHTMLParser()
        parser.feed(text)
        parser.close()
        return parser.text()


def get_poem(key_word):
    base = list()
    template = 'http://poetory.ru/content/list?{}'
    url = template.format(urllib.parse.urlencode({'query': key_word}))
    req = requests.get(url)
    soup = BeautifulSoup(req.text, "lxml")
    html_poems = soup.findAll('div', {'class': "item-text"})
    for html_poem in html_poems:
        base.append(MyHTMLParser.get_poem_text(str(html_poem)))
    return(base)


def my_main():
    base_poems = dict()
    key_words = ['дождь', 'солнечно', 'облачно', 'снегопад']
    for key_word in key_words:
        base_poems[key_word] = get_poem(key_word)
    with open('poems_base.json', 'a') as fp:
        json.dump(base_poems, fp, ensure_ascii=False)


#if __name__ == '__main__':
#    main()
