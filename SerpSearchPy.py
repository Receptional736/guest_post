
import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()
#


class SerpSearcher:

    def __init__(
        self,
        keywords: str,
        country: str,
        acceptable_tlds: str,
        language:str
    ):

        self.keywords = keywords
        self.language = language

        if country is None or country == "":
            country = 'global'
        
        if acceptable_tlds is None or acceptable_tlds == "":
            acceptable_tlds = 'all' 


        self.country = country.lower()
        self.api_key = os.getenv('SEARCH_API_KEY')
        self.domain = "google.co.uk"
        self.base_url = "https://www.searchapi.io/api/v1/search"
        self.num_results = 20
        self.page = 1
        self.acceptable_tlds = acceptable_tlds or []

        if not self.api_key:
            raise ValueError("No API key provided or found in environment.")

    def tld(self, host: str) -> Optional[str]:

        # 1. Normalise acceptable_tlds into a list
        raw = self.acceptable_tlds
        if isinstance(raw, str):
            # split on whitespace or commas
            tlds = [t.strip() for t in raw.replace(',', ' ').split() if t.strip()]
        else:
            tlds = raw
   
        # 2. Check each tld
        for tld in tlds:
            if host.endswith(tld):
                return host

        # 3. No match
        return None

    def _search_single(self, query: str, language: str) -> dict:
            
        if language == 'Native':
            if self.country == 'bg':
                self.domain = "google.bg"
                q = f'{query} AND ("пишете за нас" OR "приемаме статии" OR "изпратете статия" OR "изпратете блог" OR "изпрати статия" OR "допринесете за нашия блог" OR "изпратете публикация за гости" OR "приемане на публикации за гости" OR "изпращане на публикация за гости" OR "гост автор на публикация" OR "насоки за публикуване на гости" OR "публикуване на гост публикация" OR "публикация за гости" OR "гост автор" OR "публикуване на гости" OR "изпрати блог" OR "гостуваща статия" OR "гост блог")'

            elif self.country == 'br':
                self.domain = "google.com.br"
                q = f'{query} AND ("escreva para nós" OR "estamos aceitando artigos" OR "enviar um artigo" OR "enviar um blog" OR "enviar artigo" OR "contribua para o nosso blog" OR "diretrizes do autor" OR "enviar uma postagem de convidado" OR "aceitando postagens de convidados" OR "enviando uma postagem de convidado" OR "postagem de convidado" OR "autor convidado" OR "diretrizes de submissão" OR "enviar blog" OR "artigo convidado" OR "blog convidado")'

            else:
                q = f'{query} AND ("write for us" OR "submit a blog" OR "submit blog" OR "submit article" OR "contribute to our blog" OR "submit a guest post" OR "accepting guest posts" OR "guest post submission" OR "guest post author" OR "guest post guidelines" OR "submitting a guest post" OR "guest post" OR "guest author" OR "guest posting" OR "guest article" OR "guest blogging" OR "guest blog")'

        else:
            q = f'{query} AND ("write for us" OR "submit a blog" OR "submit blog" OR "submit article" OR "contribute to our blog" OR "submit a guest post" OR "accepting guest posts" OR "guest post submission" OR "guest post author" OR "guest post guidelines" OR "submitting a guest post" OR "guest post" OR "guest author" OR "guest posting" OR "guest article" OR "guest blogging" OR "guest blog")'



        headers = {"Authorization": f"Bearer {self.api_key}"}

        if self.country== 'global':
            params = {
                "engine":        "google",
                "q":             q,
                "google_domain": self.domain,
                "hl":            "en",
                "num":           self.num_results,
                "page":          self.page
            }

        else:

            params = {
                "engine":        "google",
                "q":             q,
                "gl":            self.country,
                "google_domain": self.domain,
                "hl":            "en",
                "num":           self.num_results,
                "page":          self.page
            }
        resp = requests.get(self.base_url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def search(self) -> dict:

        filtered_domains: List[str] = []
    
        data = self._search_single(self.keywords,self.language)

        if self.acceptable_tlds == "all":

            for result in data.get("organic_results", []):
                link = result.get("link", "")
                host = urlparse(link).netloc
                filtered_domains.append(host)
            return {"output": filtered_domains}

        else:

            for result in data.get("organic_results", []):
                link = result.get("link", "")
                host = urlparse(link).netloc
                valid = self.tld(host)
                if valid:
                    filtered_domains.append(valid)
            return {"output": filtered_domains}











