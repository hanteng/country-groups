# -*- coding: utf-8 -*-
#歧視無邊，回頭是岸。鍵起鍵落，情真情幻。
import os.path, glob
import json
import requests
import pandas as pd
import codecs

# Data source 
URL_ = "https://raw.githubusercontent.com/unicode-cldr/cldr-core/master/supplemental/territoryContainment.json"
URL_country_names_template = "https://raw.githubusercontent.com/hanteng/country-names/master/data/CLDR_country_name_{locale}.tsv"
locale_s = [ 'en', 'fr', 'zh', 'zh-Hant']

path_data = u'../data'
## Outpuing Lists
outputfn1 = os.path.join(path_data, "CLDR_all.tsv")
outputfn2 = os.path.join(path_data, "CLDR_UN_region.tsv")
outputfn3 = os.path.join(path_data, "CLDR_UN_region_names_{locale}.tsv")
outputfn4 = os.path.join(path_data, "PE_org.json")

def url_request (url):
    r = requests.get(url)
    if r.status_code == 200:
        return r
    else:
        return None 

## Retrive data directly from unicode-cldr project hosted at github
print ("Retrieve data now ...")
results = url_request (url  = URL_).json()['supplemental']
print ("Retrieved data with the version of {}".format(results['version']))

## Preprocessing 
print ("Preprocessing data now ...")

df = pd.DataFrame()
for i, k in enumerate(results['territoryContainment'].keys()):
    outcomes_split = k.split("-",1)
    if len(outcomes_split)==2:
        code, status = outcomes_split 
    else:
        if len(outcomes_split)!=1:
            print ("Warning!")
            code, status = ['warning','warning']
        else:
            code = outcomes_split[0]
            status = ""
    code_other = results['territoryContainment'][k]['_contains']
    _grouping = results['territoryContainment'][k].get('_grouping', "false")

    ## debug print
    ##print ("{}-{}->{}    {}".format(code, status, code_other, _grouping))

    df_chunk = pd.DataFrame()
    df_chunk['code_contained'] = code_other
    df_chunk['i_group'] = i 
    df_chunk['code'] = code
    df_chunk['status'] = status
    df_chunk['_grouping'] = _grouping

    df = df.append(df_chunk)

columns_order = ['i_group', 'code', 'code_contained', 'status', '_grouping']
df[columns_order].to_csv(outputfn1, sep='\t', encoding='utf-8',  header = True, index = False)

## Generating a table with UN M.49 regions and subregions.

code_start = "001"
query_temp = 'code=="{code}" and status==""'

def next_level(c):
    return list(df.query(query_temp.format(code=c))['code_contained'].sort_values())

df_w = pd.DataFrame()
for i in next_level("001"):
    for j in next_level(i):
        #print ([i,j,next_level(j)])
        df_wc = pd.DataFrame()
        df_wc['ccode'] = next_level(j)
        df_wc['rcode_sub'] = j 
        df_wc['rcode'] = i

        df_w = df_w.append(df_wc)

df_w.to_csv(outputfn2, sep='\t', encoding='utf-8',  header = True, index = False)
 

## Retrive data directly from unicode-cldr project hosted at github
print ("Retrieve country names data now ...")

#locale = "en"
for locale in locale_s:
    url = URL_country_names_template.format(locale=locale)
    df_results = pd.read_csv(url, sep='\t', encoding='utf-8',
                             na_values=[], keep_default_na = False,
                             names = ['c','n'] , index_col='c', 
                             )
    ## Construct dictionary for country/region names
    c_names = df_results.to_dict()['n'] #http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_dict.html

    df_w ['cname'] = [c_names[x] for x in list(df_w ['ccode'])]
    df_w ['r_sub'] = [c_names[x] for x in list(df_w ['rcode_sub'])]
    df_w ['rname'] = [c_names[x] for x in list(df_w ['rcode'])]

    df_w.to_csv(outputfn3.format(locale=locale), sep='\t', encoding='utf-8',  header = True, index = False)


## Generating a table with EU countries.
PE_org = dict() # PE_org: Political and economic organization
PE_org ['EU'] = list(df.query(query_temp.format(code='EU'))['code_contained'])

with codecs.open(outputfn4, encoding='utf-8', mode='w+') as fp:
    data = PE_org
    json.dump(data, fp)

