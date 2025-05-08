
import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()



class SerpSearcher:

    def __init__(
        self,
        keywords: str,
        country: str,
        acceptable_tlds: str
    ):

        self.keywords = keywords
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

    def _search_single(self, query: str) -> dict:
        
        q = f'{query} AND (""write for us"" OR ""we are accepting articles"" OR ""submit an article"" OR ""submit a blog"" OR ""submit content"" OR ""contribute to our blog"" OR ""aim for a word count"" OR ""author guidelines"" OR ""submit a guest post"" OR ""accepting guest posts"" OR ""guest post submission"" OR ""guest post author"" OR ""guest post guidelines"" OR ""submitting a guest post"" OR ""guest post"" OR ""guest author"" OR ""submission guidelines"" OR ""guest posting"")'

        headers = {"Authorization": f"Bearer {self.api_key}"}
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
    
        data = self._search_single(self.keywords)
        for result in data.get("organic_results", []):
            link = result.get("link", "")
            host = urlparse(link).netloc
            valid = self.tld(host)
            if valid:
                filtered_domains.append(valid)
        return {"output": filtered_domains}











