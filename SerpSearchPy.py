
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
        acceptable_tlds: Optional[List[str]] = None
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
        """
        Check if a host’s TLD is in the acceptable list.

        Args:
            host: Hostname (e.g. 'example.com').

        Returns:
            The original host if its TLD (with leading dot) is acceptable, else None.
        """
        if '.' not in host:
            return None
        suffix = '.' + host.rsplit('.', 1)[-1]
        return host if suffix in self.acceptable_tlds else None

    def _search_single(self, query: str) -> dict:

        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "engine":        "google",
            "q":             query,
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

