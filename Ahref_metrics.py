from __future__ import annotations
import os
import datetime
from typing import Iterable, List
import requests
from dotenv import load_dotenv
load_dotenv()



class AhrefsMetrics:

    BASE_URL = "https://api.ahrefs.com/v3"

    def __init__(
        self,
        country: str ,
        date: str,
    ):

        self.api_key = os.getenv("AHREFS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key supplied. Pass 'api_key' or set the AHREFS_API_KEY environment variable."
            )

        self.country = country.lower()
        self.date = date 

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json, application/xml",
                "Authorization": f"Bearer {self.api_key}",
            }
        )

    # --------------------------------------------------------------------- #
    # Low‑level helpers
    # --------------------------------------------------------------------- #
    def _get(self, endpoint: str, **params):
        url = f"{self.BASE_URL}/{endpoint}"
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    # --------------------------------------------------------------------- #
    # Public API methods
    # --------------------------------------------------------------------- #
    def get_organic_traffic(
        self,
        target: str
    ):
        """Return estimated monthly organic traffic for *target*. and location"""
        payload = {
            "target": target,
            "country": self.country,
            "date": self.date,
        }
        data = self._get("site-explorer/metrics", **payload)
        local_traffic = float(data.get("metrics", {}).get("org_traffic", 0))
        org_keywords = data.get('metrics').get('org_keywords',0)

        #global info
        payload = {
            "target": target,
            "date": self.date,
        }
        
        data_glob = self._get("site-explorer/metrics", **payload)
        global_traffic = float(data_glob.get("metrics", {}).get("org_traffic", 0))
        print(local_traffic,global_traffic)
        return local_traffic, local_traffic/global_traffic, org_keywords

    def get_domain_rating(
        self,
        target: str,
    ):
        payload = {
            "target": target,
            "date": self.date,
        }
        data = self._get("site-explorer/domain-rating", **payload)
        return float(data.get("domain_rating", {}).get("domain_rating", 0))

    # --------------------------------------------------------------------- #
    # Higher‑level workflows
    # --------------------------------------------------------------------- #
    def filter_links(
        self,
        links: Iterable[str],
        target_dr: float,
        target_traffic: int,
        target_ranking: int,
        target_precentage_traffic: float
    ) :

        unique_links: List[str] = list(dict.fromkeys(links))  # preserve order, drop dups

        r = []
        

        for link in unique_links:
            local_traffic, percentage_traffic, ranking_keywords = self.get_organic_traffic(link)
            dr = self.get_domain_rating(link)

            if dr >= target_dr and local_traffic >= target_traffic and ranking_keywords >= target_ranking and percentage_traffic >= target_precentage_traffic:
               
                r.append({"link":link,
                         "dr":dr,
                         "traffic":local_traffic,
                          "traffic_percent":percentage_traffic,
                          "ranking_keywords":ranking_keywords                         
                         })

        output = {'output':r}
                
        return output



