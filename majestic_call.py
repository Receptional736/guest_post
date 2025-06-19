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

    url = canonical_url(url)
    
    params = {
        "app_api_key": MAJESTIC_API_KEY,
        "cmd": "GetIndexItemInfo",
        "items": 1,          # number of items in this request
        "item0": url,       # the single item we’re querying
        "datasource": datasource  # fresh or historic
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
        'ttf2':info['TopicalTrustFlow_Topic_2']
    }
    
    return TTF



def sub_relevance_checker(target_url, client_url):
    try:
        completion = gpt_llm.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
            {"role": "developer", "content": "You are a subject analyser. Only respond with 'pass' or 'fail'. No explanation. Lowercase only."},
            {"role": "user", "content": f"If any subject in this list {target_url} is related and close match with any of subject'{client_url}', respond with 'pass'. Otherwise respond with 'fail'."}
          ]
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return 'None'