# -*- coding: utf-8 -*-
#歧視無邊，回頭是岸。鍵起鍵落，情真情幻。
# Correction: 0->ASEAN, 49-> GB, 52 ->KR 
import os.path, glob
import requests
from lxml.html import fromstring, tostring, parse
from io import StringIO, BytesIO
import codecs
import pandas as pd
import json

XML_encoding="utf-8"

# Data source 
URL_ = "http://ec.europa.eu/trade/policy/countries-and-regions/regions/euro-mediterranean-partnership/"
URL_country_names_template = "https://raw.githubusercontent.com/hanteng/country-names/master/data/CLDR_country_name_{locale}.tsv"
URL_country_names = URL_country_names_template.format(locale= 'en')


# Xpath extraction
_xpath='//*[@id="col-2"]/table/tbody/tr/td[1]/a/text()'

## Outpuing Lists
PE = 'EUROMED'
path_data = u'../data'
outputfn1 = os.path.join(path_data, "PE_org.json")
outputfn2 = os.path.join(path_data, "CLDR_UN_region.tsv")


def url_request (url):
    r = requests.get(url)
    if r.status_code == 200:
        #r.raw.decode_content = True
        return r
    else:
        print ("Downloading the data from {0} failed. Plese check Internet connections.".format(XML_src_url))
        return None

def url_local_request (url):
    fn_local = os.path.join(path_data, PE+ ".htm")
    
    print (fn_local)  #debug
    try:
        tree = parse(fn_local)
    except:
        r = url_request (url) 
        XML_src=r.content
        with codecs.open(fn_local, "w", XML_encoding) as file:
            file.write(XML_src.decode(XML_encoding))

        #from lxml.html.clean import clean_html
        #XML_src = clean_html(XML_src)
        tree = fromstring(XML_src)

    return tree

t = url_local_request(URL_)

list_country_names_Web = t.xpath(_xpath)
print (list_country_names_Web)



## Retrive data directly from unicode-cldr project hosted at github
print ("Retrieve country names data now ...")

locale = "en"
url = URL_country_names_template.format(locale=locale)
df_results = pd.read_csv(url, sep='\t', encoding='utf-8',
                         na_values=[], keep_default_na = False,
                         names = ['c','n'] , index_col='c', 
                         )
## Construct dictionary for country/region names
c_names = df_results.to_dict()['n'] #http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_dict.html
c_names_inv = {v: k for k, v in c_names.items()}

## Country names fuzzy match
from fuzzywuzzy import process

choice=[]
for i, c_name_Web in enumerate(list_country_names_Web):
    
    #found_candidates = [x for x in c_names_inv.keys() if fuzzy_match(x,c_name_Web)==True]
    found_candidate = process.extract(c_name_Web, c_names_inv.keys(), limit=1)
    found_candidate_c = c_names_inv[found_candidate[0][0]]
    choice_item = [i, c_name_Web, found_candidate, found_candidate_c]
    #print (choice_item)
    choice.append(choice_item)

import ast
done = False
while not(done):
    try:
        # Note: Python 2.x users should use raw_input, the equivalent of 3.x's input
        prn= [repr(x) for x in choice]
        print ("\n\r".join(prn))
        i = int(input("Please enter your corrections: Serial no (-1:None): "))
        if i==-1:
            print ("Done!")
            done==True
            break
        else:
            if i in range(len(choice)):
                c = input("Please enter your corrections: Country code (ISO-alpha2): ")
                choice[i][3] = c
            else:
                print("Sorry, Please revise your input.")
    except ValueError:
        print("Sorry, I didn't understand that.")
        #better try again... Return to the start of the loop
        continue
   

list_country_codes_Web = [x[3] for x in choice]
print (list_country_codes_Web)
print (list_country_names_Web)
print ("==========")

PE_org = dict()

with codecs.open(outputfn1, encoding='utf-8', mode='r+') as fp:
    lines=fp.readlines()
    PE_org = json.loads(u"".join(lines))

print (PE_org)
d={PE: list_country_codes_Web}
print(d)
PE_org.update(d)
print (PE_org)


with codecs.open(outputfn1, encoding='utf-8', mode='w') as fp:
    json.dump(PE_org, fp)
