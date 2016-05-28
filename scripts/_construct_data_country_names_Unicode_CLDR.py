# -*- coding: utf-8 -*-
#歧視無邊，回頭是岸。鍵起鍵落，情真情幻。
import os.path, glob
import json
import requests
import icu # pip install PyICU

path_data = u'../data'
## Outpuing Lists
outputfn_tsv_by_locale = os.path.join(path_data, "CLDR.tsv")


def url_request (url):
    r = requests.get(url)
    if r.status_code == 200:
        return r
    else:
        return None 


def load_json_list (lc_file, u):
    try:
        with open(lc_file, 'r', encoding="utf-8") as infile:
            _select = json.load (infile)
            print ("Loaded from local file.")
    except:
        results = url_request (url  = u)
        if results is not None:
            try:
                _select = results.json()['availableLocales']['full']
                with open(lc_file, 'w', encoding="utf-8") as outfile:
                    outfile.write("{}".format(_select).replace("'",'"'))
                print ("Loaded from designated url.")
            except:
                pass
    return _select


# Partial Selected Construction
locale_select = ['en'] # English is selected. Can be extended in the future  'zh-Hant-HK', 'zh-Hant-MO', 'zh-Hans', 'zh-Hans-SG'

## Retrive data directly from unicode-cldr project hosted at github
print ("Retrieve data now ...")
URL_CLDR_JSON_TERRITORIES = "https://raw.githubusercontent.com/unicode-cldr/cldr-localenames-full/master/main/{locale}/territories.json"
locale_json={}
for l in locale_select:
    results = url_request (url  = URL_CLDR_JSON_TERRITORIES.format(locale=l))
    if results is not None:
        try:
            locale_json [l] = results.json()['main'][l]['localeDisplayNames']['territories']
        except:
            pass

## Preprocessing and Generating lists
print ("Preprocessing data now ...")
ITEM_NAME_CODE = "{name}[{code}]"
ITEM_CODE_NAME = "{code}:{name}"

outputlist_territories={}
for key, value in locale_json.items():
    ### Remove UN regional codes (three digits)  
    value_new = {k: v for k, v in value.items() if k.isdigit() is not True}

    c_n=dict()
    for k, v in value_new.items():
        ### Remove -alt-variant and -alt-short
        if len(k)>2:
            if "-alt-variant" in k:
                print ("not using:{}".format([k,v]))
                pass
            if "-alt-short" in k:  ## Using -alt-short if exists
                k=k.replace("-alt-short", "")
                print ("using:{}".format([k,v]))
                c_n.update({k:v})
        else:
            if k in c_n.keys():
                print ("not using:{}".format([k,v]))
            else:
                c_n.update({k:v})

   
    ### Sort by IBM's ICU library, which uses the full Unicode Collation Algorithm
    print (key)
    collator = icu.Collator.createInstance(icu.Locale('{lc}.UTF-8'.format(lc=key)))
    c_n_keys_sorted = sorted(list(c_n.keys()))

    outputlist_territories [key]  =  [(x, c_n[x]) for x in c_n_keys_sorted]

import pandas as pd
df = pd.DataFrame(outputlist_territories['en'])

df.to_csv(outputfn_tsv_by_locale.format(locale='en'), sep='\t', encoding='utf-8',  header = False, index = False)
