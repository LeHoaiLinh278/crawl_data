#%%
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time
import json
from tqdm.notebook import tqdm
import os

base_url = 'https://nhattao.com/'
url = 'https://nhattao.com/f/may-tinh.553/'

#%%
def get_bs(url):
    try:
        html = urlopen(url)
        bs = BeautifulSoup(html, 'html.parser')
    except:
        bs = None
    return bs

#%%
#get link category
def get_link_category(url):
    bs = get_bs(url)
    links = bs.find_all('h3', {'class': 'nodeTitle'})
    dict_category = {}
    for link in links:
        link_category = link.find_all('a')
        dict_category[link_category[0].get_text()] = base_url + link_category[0].attrs['href']
    return dict_category

dict_categories = get_link_category(url)
print(dict_categories)

# %%
#get all links
def get_next_page(url):
    bs = get_bs(url)
    next_page = None
    page = bs.find_all('div', {'class': 'pageNavLinkGroup'})[0]
    find_nextpages = page.find_all('a')
    for find_nextpage in find_nextpages:
        if 'Sau' in find_nextpage.get_text():
            next_page = base_url + find_nextpage.attrs['href']
    return next_page

def get_alllink_item(url_page):
    bs = get_bs(url_page)
    link_item = []
    cardlist = bs.find('div', {'class': 'Nhattao-CardList'})
    links = cardlist.find_all('a', {'class': 'Nhattao-CardItem--image'})
    for link in links:
        link_item.append(base_url + link.attrs['href'])
    return link_item
#%%
dict_alllink_item = {}
for key,link in dict_categories.items():
    link_current = link
    link_items = []
    while link_current != None:
        link_items.extend(get_alllink_item(link_current))
        link_current = get_next_page(link_current)
        time.sleep(5)
    print(key)
    print(len(link_items))
    dict_alllink_item[key] = link_items
    print('-------------------------------')
    #break

# %%
df_alllink_item = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in dict_alllink_item.items() ]))
print(df_alllink_item.info())
df_alllink_item.to_csv('nhattao_computer_alllink.csv', index=False)

# %%
df_alllink_item = pd.read_csv('nhattao_computer_alllink.csv')
print(df_alllink_item.info())

#%%
# Crawl data
def get_title_item(bs):
    try:
        title = bs.find_all('h2', {'class' : 'threadview-header--title'})[0].get_text()
    except:
        title = None
    return title

def get_price_item(bs):
    try:
        price_item = bs.find_all('p', {'threadview-header--classifiedPrice'})[0].get_text()
    except:
        price_item = None

    return price_item

def get_device_status_item(bs):
    dict_status = {}
    try:
        meta = bs.find('div', {'class' : 'TTC_classifiedMeta'})
        cards = meta.find_all('dl')
        for card in cards:
            key_card  = card.find('dt').get_text().strip()
            value_card = card.find('dd').get_text().strip()
            dict_status[key_card] = value_card
    except:
        pass
    return dict_status

def get_number_phone_item(bs):
    try:
        number_phone = bs.find('a', {'class' : 'threadview-header--contactPhone'}).get_text().strip()
    except:
        number_phone = None
    return number_phone

def get_address_item(bs):
    try:
        address = bs.find('span', {'class' : 'address'}).get_text().strip()
    except:
        address = None
    return address

def get_user_item(bs):
    dict_user = {}
    try:
        user_class = bs.find('a', {'class' : 'username seller-name'})
        link_user = base_url + user_class.attrs['href']
        name_user = user_class.find('span').get_text().strip()
        dict_user[name_user] = link_user
    except:
        pass
    return dict_user

def get_description_item(bs):
    try:
        description = json.dumps(bs.find('blockquote', {'class': 'messageText SelectQuoteContainer ugc baseHtml'}).get_text().strip(), ensure_ascii=False)
    except:
        description = None
    return description


#%%
column_categories = df_alllink_item.columns
print(column_categories)

#%%
column_item = ['category', 'title', 'price', 'device_status',
                'number_phone', 'address', 'user', 'description', 'link_item']
df_item = pd.DataFrame(columns=column_item)
if os.path.isfile('nhattao_computer_data.csv'):
    print('file save data:....')
    df_item = pd.read_csv('nhattao_computer_data.csv')
else:
    df_item.to_csv('nhattao_computer_data.csv', index=False)
#%%
def update_link_crawl(alllink_category, link_item_saved):
    i = 0
    list_alllink = alllink_category.values.tolist()
    if len(link_item_saved) != 0:
        for link in link_item_saved:
            if link in list_alllink:
                i += 1
                list_alllink.remove(link)
    print('Number link saved: ', i)
    return  list_alllink
    
# %%
for column_category in tqdm(column_categories):
    alllink_item = df_alllink_item[column_category].dropna()
    alllink_item = update_link_crawl(alllink_item, df_item['link_item'])
    for link in tqdm(alllink_item):
        data_item = {}
        bs = get_bs(link)
        time.sleep(5)
        if bs != None:
            data_item['category'] = column_category
            #print('category_item: ', data_item['category'])
            data_item['title'] = get_title_item(bs)
            #print('title_item: ', data_item['title'])
            data_item['price'] = get_price_item(bs)
            #print('price_item: ', data_item['price'])
            data_item['device_status'] = get_device_status_item(bs)
            #print('device_status_item: ', data_item['device_status'])
            data_item['number_phone'] = get_number_phone_item(bs)
            #print('number_phone_item: ', data_item['number_phone'])
            data_item['address'] = get_address_item(bs)
            #print('address_item: ', data_item['address'])
            data_item['user'] = get_user_item(bs)
            #print('user_item: ', data_item['user'])
            data_item['description'] = get_description_item(bs)
            #print('description_item: ', data_item['description'])
            data_item['link_item'] = link
            if data_item['title'] != None:
                df_item = df_item.append(data_item, ignore_index=True)
                df_item.to_csv('nhattao_computer_data.csv', index=False)
                df_item = pd.read_csv('nhattao_computer_data.csv')
            #print('------------------------------')
        else:
            print(link)
        #break
    #break
# %%
print(df_item.info())
df_item.to_csv('nhattao_computer_data.csv', index=False)