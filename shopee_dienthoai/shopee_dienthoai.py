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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

base_url = 'https://shopee.vn'
url = 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979'

#%%
# install ChromeDriver( use to download ChromeDriver)
# https://stackoverflow.com/questions/60296873/sessionnotcreatedexception-message-session-not-created-this-version-of-chrome

# from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
# driver = webdriver.Chrome(ChromeDriverManager().install())

#%%

# chrome_options = Options()
# chrome_options.add_argument("--headless")
# driver = webdriver.Chrome(
#     executable_path='./chromedriver',
#     options=chrome_options)

# driver.get('https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979')
# time.sleep(2)
# driver.find_element_by_class_name('shopee-mini-page-controller__next-btn').click()
# next_link = driver.current_url
# driver.close()
# print(next_link)


# %%
def scroll_page(driver):
    SCROLL_PAUSE_TIME = 1
    last_height = driver.execute_script("return document.body.scrollHeight")
    new_height = 500 
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, arguments[0]);", new_height) 

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        new_height = new_height + 500 # height when scroll page Ex:500
        if new_height >= last_height:
            driver.execute_script("window.scrollTo(0, arguments[0]);", last_height) 
            break

def render_html_page(url_page, scroll=True):
    """
        url_page: url input of page
        scroll : True when it's use scroll page. Default True
    """
    if scroll:
        chrome_options = Options()
        #chrome_options.add_argument("--headless")  # No use UI, It has to be commented when using page scroll
        driver = webdriver.Chrome(
            executable_path='./chromedriver',)
        #    options=chrome_options)
        driver.get(url_page)
        time.sleep(10)
        scroll_page(driver)
    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # No use UI, It has to be commented when using page scroll
        driver = webdriver.Chrome(
            executable_path='./chromedriver',
            options=chrome_options)
        driver.get(url_page)
        time.sleep(10)
    try:
        bs = BeautifulSoup(driver.page_source, 'html.parser')
    except:
        bs = None
    driver.quit()
    return bs
#%%
def get_next_page(url, classname):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(
        executable_path='./chromedriver',
        options=chrome_options)

    driver.get(url)
    try:
        element = WebDriverWait(driver, 120).until(
                        EC.presence_of_element_located((By.CLASS_NAME, classname)))
    finally:
        driver.find_element_by_class_name(classname).click()
        next_link = driver.current_url
        driver.close()
        driver.quit()
        if next_link != url:
            return next_link
        else:
            next_link = None
            return next_link
#%%
def get_alllink_item(url_page):
    try:
        bs = render_html_page(url_page,scroll=True)
        link_item = []
        list_item = bs.find('div', {'class': 'shopee-search-item-result'})
        links = list_item.find_all('div', {'class' : 'shopee-search-item-result__item'})
        for link in links:
            link_a = link.find('a', {"data-sqe" : "link"})
            if 'href' in link_a.attrs:
                link_item.append(base_url + link_a.get('href'))
                #print(str((base_url + link_a.get('href')).encode('utf-8', 'ignore')))
    except:
        get_alllink_item(url_page)
    return link_item
        

#%%
all_links = []
current_link = url
while current_link != None:
    print(current_link)
    all_links.extend(get_alllink_item(current_link))
    current_link = get_next_page(current_link, 'shopee-mini-page-controller__next-btn')
    time.sleep(10)
    #print('-------------------------------------')
    #break
print(len(all_links))    

# %%
all_links_item = pd.DataFrame({'link' : all_links})
all_links_item.head(5)
all_links_item.to_csv('shopee_dienthoai_alllink.csv', index=False)

#%%
all_links_item = pd.read_csv('shopee_dienthoai_alllink.csv')

#%%
column_item = ['category', 'title', 'price', 'product_detail',
                'product_description', 'user','link_item']
df_item = pd.DataFrame(columns=column_item)
if os.path.isfile('shopee_dienthoai_data.csv'):
    print('file save data:....')
    df_item = pd.read_csv('shopee_dienthoai_data.csv')
else:
    df_item.to_csv('shopee_dienthoai_data.csv', index=False)

#%%
def get_title_item(bs):
    try:
        title = bs.find('div', {'class': 'qaNIZv'}).get_text()
    except:
        title = None
    return title

def get_price_item(bs):
    try:
        price = bs.find('div', {'class' : '_3n5NQx'}).get_text()
    except:
        price = None
    return price

def get_product_detail_item(bs):
    product_detail = {}
    try:
        details = bs.find_all('div', {'class': 'kIo6pj'})
        for detail in details:
            list_detail = [d.get_text() for d in detail]
            product_detail[list_detail[0]] = list_detail[1:]
    except:
        pass
    return product_detail
def get_product_description_item(bs):
    try:
        descriptions = bs.find('div', {'class': '_2u0jt9'})
        list_description = [json.dumps(description.get_text().strip(), ensure_ascii=False) for description in descriptions]
        product_description = list_description
    except:
        product_description = None
    return product_description
def get_user_item(bs):
    user_item = {}
    try:
        name_user = bs.find('div', {'class': '_3Lybjn'}).get_text().strip()
        link_user = base_url + bs.find('a', {'class': '_136nGn'}).attrs['href']
        user_item[name_user] = link_user
    except:
        pass
    return user_item

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
alllink_item = update_link_crawl(all_links_item['link'], df_item['link_item'])
for link_item in tqdm(alllink_item):
    data_item = {}
    bs = render_html_page(link_item,scroll=True)
    if bs != None:
        data_item['category'] = 'Dien Thoai'
        #print('category_item: ', data_item['category'])
        data_item['title'] = get_title_item(bs)
        #print('title_item: ', data_item['title'])
        data_item['price'] = get_price_item(bs)
        #print('price_item: ', data_item['price'])
        data_item['product_detail'] = get_product_detail_item(bs)
        #print('product_detail: ', data_item['product_detail'])
        data_item['product_description'] = get_product_description_item(bs)
        #print('product_description: ', data_item['product_description'])
        data_item['user'] = get_user_item(bs)
        #print('user_item: ', data_item['user'])
        data_item['link_item'] = link_item
        if data_item['title'] != None:
            df_item = df_item.append(data_item, ignore_index=True)
            df_item.to_csv('shopee_dienthoai_data.csv', index=False)
            df_item = pd.read_csv('shopee_dienthoai_data.csv')
        #print('----------------------------------------------')
    else:
        print(link_item)
    #if idx == 2:
    #    break

# %%
