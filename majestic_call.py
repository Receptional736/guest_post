import os
import sys
import requests
from dotenv import load_dotenv
from openai import OpenAI
from urllib.parse import urlparse

load_dotenv()
gpt_llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
MAJESTIC_API_KEY = os.getenv('MAJESTIC_API_KEY')
ENDPOINT = "https://api.majestic.com/api/json"  



def canonical_url(raw: str, *, keep_scheme: bool = False, strip_www: bool = True) -> str:

    if "://" not in raw:
        raw = "http://" + raw        
    
    p = urlparse(raw.lower())
    host = p.netloc or p.path     
    
    if strip_www and host.startswith("www."):
        host = host[4:]
    
    if keep_scheme:
        scheme = p.scheme if p.scheme else "http"
        return f"{scheme}://{host}"
    
    return host




def get_ttf(url: str, datasource: str = "fresh"):

    #url = canonical_url(url)
    
    params = {
        "app_api_key": MAJESTIC_API_KEY,
        "cmd": "GetIndexItemInfo",
        "items": 1,
        "item0": url,
        "datasource": datasource,
        "DesiredTopics": 10,      # up to 30/20/10 as per docs
        "AddAllTopics": 1         # optional, gives the 'TrustCategories' field
    }

    try:
        resp = requests.get(ENDPOINT, params=params, timeout=30)
        resp.raise_for_status()        # raises if HTTP ≠ 200
        payload = resp.json()

    except Exception as e:
        return {'ttf0': '', 'ttf1': '', 'ttf2': ''}

    info = payload["DataTables"]["Results"]["Data"][0]

    TTF = {
        'ttf0':info['TopicalTrustFlow_Topic_0'],
        'ttf1':info['TopicalTrustFlow_Topic_1'],
        'ttf2':info['TopicalTrustFlow_Topic_2'],
        'ttf3':info['TopicalTrustFlow_Topic_3'],
        'ttf4':info['TopicalTrustFlow_Topic_4']
    }
    
    return TTF



def sub_relevance_checker(prospect, target):
    try:

        for pros in prospect.values():
            for targ in target.values():
                if pros == targ:
                    return 'pass'

        return 'fail'
    except Exception as e:
        return 'fail'