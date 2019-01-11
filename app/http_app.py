import tornado.ioloop
import tornado.web
import os
import sys
import requests
from lxml import html
from bs4 import BeautifulSoup
from collections import Counter
import math
from string import punctuation
from os import path
from wordcloud import WordCloud
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import cgi
import io
import time
from urllib.parse import urlparse
import base64
import dbconnection
import random

# show db  
class dbHandler(tornado.web.RequestHandler):
    '''handle the connection to the DB from /admin - site  
        
    '''

    def get(self):

        mydb=dbconnection.connectdb()
        words = dbconnection.readData(mydb)

        strHTML='''
            <html>
            <head>
            </head>
            <style>
            center { 
              //height: 200px;
              position: absolute;top:10px;left:5px;right:5px;bottom:10px;
              //border: 3px solid green; 
            }
            {
              color:grey
            }
            </style>
              <body bgcolor="white">'''
        wStr=str()
        for w in words:
            # wStr += '''<p>word {0} : count {1}</p>'''.format(w[0], w[1])
            strHTML += '<a>{} {}</a><br>'.format(w[0], w[1])
            # strHTML += wStr
            strHTML += '''
              </body>
            </html>'''

        self.write(strHTML)

class wordHandler(tornado.web.RequestHandler):
    def post(self):
        '''handle the 'url' - argument from the main page  
            
        - write the generated words to the db
        '''

        url = self.get_argument('my_url')
        if (url):

            total_words = int()
            words={}
            total_words, words = self.parseHtml(url)
            mydb=dbconnection.connectdb()
            if not dbconnection.existsTable(mydb, 'wordy'):
                dbconnection.createTable(mydb)

            # change 'Counter' to 'Dict'
            data = dict(words)
            ret = dbconnection.writeData(mydb, data)

            self.writeWordCloud(words)
            ret = dbconnection.closedb(mydb)

        else:
            self.write('<center><p><H2>somethings wrong with the url</H2></p></center>')


    def createWordCloudImage(self, words):
        '''create the wrodcloud image  

        Keyword arguments:
        words -- wordcloud object
        '''

        word_cloud = WordCloud(width=1024, height=768).generate_from_frequencies(words)
        img = word_cloud.to_image()

        return img


    def writeWordCloud(self, words):
        '''write the word cloud to the web page 

        Keyword arguments:
        words -- wordcloud object
        '''

        img = self.createWordCloudImage(words)

        strHTML='''
        <html>
        <head>
        </head>
        <style>
        .center { 
          //height: 200px;
          position: absolute;top:10px;left:5px;right:5px;bottom:10px;
          //border: 3px solid green; 
        }
        .center img {
          margin: 0;
          position: absolute;
          top: 50%;
          left: 50%;
          -ms-transform: translate(-50%, -50%);
          transform: translate(-50%, -50%);
          max-width: 100%;
          max-height: 100%;
        }
        </style>
          <body bgcolor="black">
            <div class="center">'''

        bio = io.BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        data_url = base64.b64encode(bio.read()).decode('ascii')
        strHTML += '''<img src="data:image/png;base64,{0}">'''.format(data_url)

        strHTML += '''
            </div>
          </body>
        </html>'''
        
        self.write(strHTML)


    def parseByTag(self, html, tag):
        '''parse HTML by tag

        Keyword arguments:
        html -- BeautifulSoup object
        tag  -- string 
        '''

        total_words=int()
        
        words = []

        for i, t in enumerate(html.select(tag)):
            for j, word in enumerate(t.text.split(' ')):
                for k, w in enumerate(word.split('\n')):
                    w = w.rstrip(punctuation)
                    w = w.rstrip(' ')
                    if len(w)>1 and w is not  None and len(w)<255:
                        total_words+=1
                        words.append(w)

        
        return  total_words, words

    def parseHtml(self, url):
        '''parse all the text from the website html

        Keyword arguments:
        url  -- string 
        '''

        words = []
        total_words = int()

        o = urlparse(url)
        if o.netloc is '' :
            url = 'http://' + url

        r = requests.get(url)
        html = BeautifulSoup(r.content, features="lxml")
        total_words, w = self.parseByTag(html, 'div')
        words.extend(w)
        t_w, w = self.parseByTag(html, 'li')
        total_words += t_w
        words.extend(w)
        t_w, w = self.parseByTag(html, 'a')
        total_words += t_w
        words.extend(w)
        t_w, w = self.parseByTag(html, 'p')
        total_words += t_w
        words.extend(w)

        count = Counter(words)

        return total_words, count



class MainHandler(tornado.web.RequestHandler):
    '''
    starting point off the application
    '''
    def get(self):

        self.render("index.html")


def make_app():

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/wordy", wordHandler),
        (r"/admin", dbHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


