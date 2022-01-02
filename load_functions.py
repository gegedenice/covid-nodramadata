#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import urllib3
from bs4 import BeautifulSoup
import json

###-----FUNCTIONS TO LAOS LOCAL AND EXTERNAL DATA---###
http = urllib3.PoolManager()

def chain(start, *funcs):
    res = start
    for func in funcs:
        res = func(res)
    return res

@st.cache(suppress_st_warning=True)
def load_json_data(url,dataset,nrows):
    params = {'dataset': dataset,'rows': nrows}
    r = http.request(
        'GET',
        url,
        fields=params)
    data = json.loads(r.data.decode('utf-8'))
    return data

@st.cache(suppress_st_warning=True)
def load_csv_data(url,dataset):
    data = pd.read_csv(url+dataset,sep=";",encoding='utf8')
    return data

@st.cache(suppress_st_warning=True)
def load_excel_data(filename):
    data = pd.read_excel("data/"+filename+".xlsx")
    return data

@st.cache(suppress_st_warning=True)
def html_scrapper(url,params,table_num):
    http = urllib3.PoolManager()
    headers = { 'accept':'*/*',
                'accept-encoding':'gzip, deflate, br',
                'accept-language':'en-GB,en;q=0.9,en-US;q=0.8,hi;q=0.7,la;q=0.6',
                'cache-control':'no-cache',
                'dnt':'1',
                'pragma':'no-cache',
                'referer':'https',
                'sec-fetch-mode':'no-cors',
                'sec-fetch-site':'cross-site',
                'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    }
    f = http.request('GET', url, headers=headers, fields=params).data
    soup = BeautifulSoup(f, 'html.parser')
    res = []
    for row in soup.findAll('table',{ "frame" : "box"})[int(table_num)].tbody.findAll('tr'):
        td = row.find_all('td')
        rows = [tr.text.strip() for tr in td if tr.text.strip()]
        res.append(rows)
    df = pd.DataFrame(res)
    df = df.drop(df.index[len(df)-1]) #remove the last row of %
    return df
