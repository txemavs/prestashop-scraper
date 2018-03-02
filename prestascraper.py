# -*- coding: utf-8 -*-
import os
import json
import re
import sys
import shutil
import decimal
import requests
import datetime
from bs4 import BeautifulSoup


def encoded(x): 
    return unicode(x.decode('utf-8')).encode('utf-8')


class Section(object):
    ref = None
    name = ""
        

class Group(object):
    section = None
    ref = None
    name = ""
                

class Product(object):
    group = None
    ref = None
    sku = None
    ean = None
    name = ""

                
class PrestaShopScraper(object):

    def get_section(self, node):
        link = node.find('a')
        if link.get("href")=="/": return
        x = Section()
        href = link.get("href").replace(self.http,"").split("-")
        href[0] = href[0].replace("/","")
        x.ref = href[0]
        x.link = "-".join(href)
        span = link.find('span')
        x.name = span.text
        print "%s - %s" % (x.link, span.text)
        return x

    
    def get_group(self,node):
        x = Group()
        href = node.get("href").replace(self.http,"").split("-")
        href[0] = href[0].replace("/","")
        x.ref = href[0]
        x.link = "-".join(href)
        span = node.find('span')
        x.name = span.text
        print "    %s - %s" % (x.link, span.text)
        return x


    def get_product(self, node):
        x = Product()
        link = node.find('a', {"class":"product_img_link"})
        href = link.get("href").replace(self.http,"").split("-")
        href[0] = href[0].replace("/","")
        x.ref = href[0]
        x.link = "-".join(href)
        x.ean = href[-1].replace(".html","")
        img = link.find('img')
        x.image = img.get('src')
        if "default-home_default.jpg" in x.image:
            x.image=None
        x.name = link.get('title')

        if x.image is not None:
            filename = os.path.join("DECA",x.ean+".jpg")
            if os.path.exists(filename): return x
            
            resp = self.session.get(link.get("href"))
            soup = BeautifulSoup(resp.text, "html.parser")
            scripts = soup.find_all('script')
            for script in scripts:
                s = u"%s" % script.string
                if not "var sharing_img" in s: continue

                for line in s.split('\n'):
                    if line[0:15]=="var sharing_img":
                        src = line.split("'")[1]
                        print "    %s - %s -> %s " % (x.ean, x.name, src)
                        response = requests.get(src, stream=True)
                        with open(filename, 'wb') as jpg_file:
                            shutil.copyfileobj(response.raw, jpg_file)
                            del response
                        return x
        return x


        
    def __init__(self, web):
        self.http = web
        print "Crawling %s" % self.http
        self.session = requests.session()
        html = self.session.get(self.http)
        self.pattern = re.compile('var sharing_img = (.*?);')
        

    def get(self, url='', params=None):
        return self.session.get(self.http+url, params=params)


    def home(self):
        print "Reading %s" % self.http
        groups = []
        resp = self.get()
        soup = BeautifulSoup(resp.text, "html.parser")
        nav = soup.find("div", {"class":"nav-container"})
        
        for parent in nav.find_all("div", {"class":"parentMenu"}):            
            section = self.get_section(parent)
            if section is None: continue
            popup = soup.find("div", {"id":"popup"+section.ref})
            for item in popup.find_all("a", {"class":"itemMenuName"}):
                group = self.get_group(item)
                groups.append(group)

        for g in groups:
            self.group(g)


    def group_page(self, soup):
        products = soup.find("ul", {"class": "product_list"})
        if products is None:
            return
        
        for product in products.find_all("div",{"class":"product-container"}):
            self.get_product(product)

        follow = soup.find("li", {"id":"pagination_next_bottom"})
        if follow is not None:
            cls=""
            if follow.has_attr('class'):
                cls = follow.get('class')
            if "disabled" in cls: return
                
            link = follow.find('a')
            if link is None: return
            href = link.get("href")
            if href is None: return
            print "Reading page %s" % href
            resp = self.get(href)
            soup = BeautifulSoup(resp.text, "html.parser")
            self.group_page(soup)


    def group(self, group):
        print "Reading %s" % group.link
        resp = self.get("/"+group.link)
        soup = BeautifulSoup(resp.text, "html.parser")
        self.group_page(soup)
            


x = PrestaShopScraper("http://example.com")
x.home()

