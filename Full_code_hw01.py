import urllib
import requests
import json
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def get_data(make):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/" + make + "/vehicletype/passenger%20car?format=json"
    req = urllib.request.Request(url=url, headers=headers)
    json_obj = urllib.request.urlopen(req)
    data = json.load(json_obj)
    #print(json_obj)
    result = (data)['Results']
    #print(result)
    return result

def fetch_price(brand,model):
    sum=0
    count=0
    url = "https://www.truecar.com/new-cars-for-sale/listings/" + brand+ "/"+model + "/location-boston-ma/"
    print(url)
    html= urllib.request.urlopen(url).read()
    soup= BeautifulSoup(html, features="html.parser")
    avail = soup.find('h4',{'data-qa':'Heading'}).get_text()
    if avail == "You filtered out all available listings.":
        print(url,"No Price Available")
        return
    card=soup.find_all(attrs={"data-test" : "vehicleListing"})
    for item in card:
        name = item.find('h4',{"data-test":"vehicleListingCardTitle"}).get_text()
        price = item.find('h4',{"data-test":"vehicleListingPriceAmount"}).get_text()
        if re.search(model,name, re.IGNORECASE):
            price = price.replace('$', '')
            price = price.replace(',', '')
            sum=sum+int(price)
            count=count+1
        else:
            print(url,"error")
    if count == 0:
        print(url,"No available price")
        return
    else:
        return sum/count

def fetch_used_price(brand,model):
    count=0
    url = "https://www.truecar.com/used-cars-for-sale/listings/" + brand+ "/"+model + "/location-boston-ma/"
    html= urllib.request.urlopen(url).read()
    soup= BeautifulSoup(html, features="html.parser")
    avail = soup.find('h4',{'data-qa':'Heading'}).get_text()
    if avail == "You filtered out all available listings.":
        print(url,"No Price Available")
        return "-"
    card=soup.find_all(attrs={"data-test" : "vehicleListing"})
    year = list()
    price_set = list()
    for item in card:
        name = item.find('h4',{"data-test":"vehicleListingCardTitle"}).get_text()
        price = item.find('h4',{"data-test":"vehicleListingPriceAmount"}).get_text()
        if re.search(model,name, re.IGNORECASE):
            price = price.replace('$', '')
            price = price.replace(',', '')
            if price != "N/A":
                count=count+1
                year.append(str(name[0:4]))
                price_set.append(int(price))
                dict = {"year": year, "price": price_set}
                data = pd.DataFrame(dict)
        else:
            print(url,"error")
    if count == 0:
        print(url,"No available price")
        return "-"
    else:
        r_year = data.groupby('year').mean()
        r_year = pd.DataFrame(r_year)
        y= r_year['price'].index.tolist()
        p= r_year['price'].values.tolist()
        index = range(0,1)
        df=pd.DataFrame(index=index, columns=['2020','2019','2018','2017','2016','2015','2014','2013','2012','2011','2010','2009','2008'])
        i=0
        for item in y:
            if item in "'2020','2019','2018','2017','2016','2015','2014','2013','2012','2011','2010,'2009','2008'":
                df.loc[0,item] = p[i]
                i=i+1
        return df.values.tolist()


import csv

with open('Manufacture(top30).csv')as m:
    m_csv=csv.reader(m)
    headers=next(m_csv)
    for rows in m_csv:
        make = rows[1].replace(" ", "%20")
        done = 0
        with open('record.csv')as t:
            t_csv = csv.reader(t)
            for rec in t_csv:
                if rec[0] == make:
                    done = 1
                    break
        result=get_data(make)
        if make == None:
            print('Manufacure Error')
        if done == 1:
            continue
        else:
            for item in result:
                brand = item['Make_Name'].lower()
                model = item['Model_Name'].lower()
                brand = brand.replace(" ","-")
                model = model.replace(" ",'-')
                new = fetch_price(brand,model)
                row = [item['Make_ID'], item['Make_Name'], item['Model_ID'], item["Model_Name"]]
                if new !=  None:
                    used = fetch_used_price(brand,model)
                    row = [item['Make_ID'],item['Make_Name'],item['Model_ID'],item["Model_Name"], new ]
                    for i in used:
                        row.extend(i)
                    spec = item['Make_Name'].upper() + " " + item['Model_Name']
                    with open('all_alpha_20.csv')as m:
                        m_csv = csv.reader(m)
                        headers = next(m_csv)
                        for info in m_csv:
                            if spec in info[0]:
                                row.append(info[1])
                                row.append(info[2])
                                row.append(info[10])
                                row.append(info[11])
                                break
                print(row)
                with open('model.csv', 'a')as f:
                    f_csv = csv.writer(f)
                    f_csv.writerow(row)
            with open('record.csv', 'a')as r:
                r_csv = csv.writer(r)
                r_csv.writerow([make])


data = pd.read_csv("model.csv", index_col=3)
data['2017'] = data['2017'].apply(pd.to_numeric, errors = 'coerce')
valid = data.loc[:,'MSRP']>0
v_df = data.loc[valid,:]
price = v_df.iloc[:,4:14]
percent = price.pct_change(axis='columns',fill_method='backfill')
percent = percent[1:]
res = pd.concat([v_df,percent,percent.mean(1)],axis=1, join_axes=[v_df.index])

res.columns = ['Make_ID','Make_Name','Model_ID','MSRP','2020','2019','2018','2017','2016','2015','2014','2013','2012','2011','2010','2009','2008','Displacement','Cylinder','Vehicle Class','EPA','-','n-u','u2019','u2018','u2017','u2016','u2015','u2014','u2013','u2012','ave']

# MSRP-- ave
n_u= res.sort_values(by ='ave',ascending=False)
p_nu=n_u.iloc[:,[3,-1]]
print(p_nu)
p_nu.plot(kind='scatter', x='MSRP', y='ave')
plt.show()

# MSRP-- ave
bran_ave=n_u.groupby('Make_Name').mean()
bran_ave= bran_ave.sort_values(by ='ave',ascending=False)
bran_ave = bran_ave['ave']
bran_ave.plot(kind='bar')
plt.show()

# vc-ave
bran_ave=res.groupby('Vehicle Class').mean()
bran_ave= bran_ave.sort_values(by ='ave',ascending=False)
bran_ave = bran_ave['ave']
bran_ave.plot(kind='bar')
plt.show()

# cy-ave
bran_ave=res.groupby('Cylinder').mean()
bran_ave = bran_ave['ave']
bran_ave.plot(kind='bar')
plt.show()

# top model-ave
n_u= res.sort_values(by ='ave',ascending=False)
p_nu=n_u.iloc[5:25,[-1]].T
print(p_nu)
p_nu.plot(kind = 'bar')
plt.show()

#BRAND - price
bran_ave=res.groupby('Make_Name').mean()
bran_ave= bran_ave.sort_values(by ='MSRP',ascending=False)
bran_ave = bran_ave['MSRP']
bran_ave.plot(kind='bar')
plt.show()
