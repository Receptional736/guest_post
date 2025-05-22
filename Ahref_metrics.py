from __future__ import annotations

import os
from typing import Iterable, List, Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv

load_dotenv()


class AhrefsMetrics:

    BASE_URL = "https://api.ahrefs.com/v3"

    # ------------------------------------------------------------------ #
    # construction
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        country: str,
        date: str,
        *,
        max_workers: int = 20,          # threads used for concurrency
        connect_timeout: int = 3,
        read_timeout: int = 30,
    ):
        self.api_key: str = os.getenv("AHREFS_API_KEY") or ""
        if not self.api_key:
            raise ValueError("Set the AHREFS_API_KEY env var.")

        self.country = (country or "global").lower()
        self.date = date
        self.timeout: Tuple[int, int] = (connect_timeout, read_timeout)

        # one Session shared by all threads
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json, application/xml",
                "Authorization": f"Bearer {self.api_key}",
            }
        )

        # fast TLS reuse + retries
        adapter = HTTPAdapter(
            pool_connections=max_workers,
            pool_maxsize=max_workers,
            max_retries=Retry(total=3, backoff_factor=1),
        )
        self.session.mount("https://", adapter)

        self.max_workers = max_workers

    # ------------------------------------------------------------------ #
    # low-level helper
    # ------------------------------------------------------------------ #
    def _get(self, endpoint: str, **params) -> Dict[str, Any]:
        """Thin wrapper around requests-Session.get with error handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # public API calls
    # ------------------------------------------------------------------ #
    def get_organic_traffic(self, target: str) -> Tuple[float, float, int]:
        """Return local traffic, local/global ratio, number of ranking kws."""
        # local
        pl_local = {"target": target, "date": self.date}
        if self.country != "global":
            pl_local["country"] = self.country
        data_local = self._get("site-explorer/metrics", **pl_local)

        # global
        pl_global = {"target": target, "date": self.date}
        data_glob = self._get("site-explorer/metrics", **pl_global)

        local_traffic = float(data_local.get("metrics", {}).get("org_traffic", 0))
        global_traffic = float(data_glob.get("metrics", {}).get("org_traffic", 0))
        ranking_kws = int(data_local.get("metrics", {}).get("org_keywords", 0))

        ratio = 0.0 if global_traffic == 0 else local_traffic / global_traffic
        return local_traffic, ratio, ranking_kws

    def get_domain_rating(self, target: str) -> float:
        data = self._get(
            "site-explorer/domain-rating",
            target=target,
            date=self.date,
        )
        return float(data.get("domain_rating", {}).get("domain_rating", 0))

    # ------------------------------------------------------------------ #
    # one-domain worker used by the thread pool
    # ------------------------------------------------------------------ #
    def _collect_one(self, link: str) -> Tuple[str, Dict[str, Any]]:
        """Fetch all metrics needed for a single link; returns raw data."""
        local_traffic, pct, kw = self.get_organic_traffic(link)
        dr = self.get_domain_rating(link)
        return link, {
            "dr": dr,
            "traffic": local_traffic,
            "traffic_percent": pct,
            "ranking_keywords": kw,
        }

    # ------------------------------------------------------------------ #
    # high-level workflow
    # ------------------------------------------------------------------ #
    def filter_links(
        self,
        links: Optional[Iterable[str]],
        *,
        mx_dr: float = 0.0,
        mn_dr: float = 100.0,
        target_traffic: int = 0,
        target_ranking: int = 0,
        target_precentage_traffic: float = 0.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Return the subset of links that meet all the supplied thresholds."""
        if not links:
            result = {'output': [{'link': '','dr': '','traffic': '','traffic_percent': '','ranking_keywords': ''}]}
            return result

        unique_links: List[str] = list(dict.fromkeys(links))
        passed: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._collect_one, link): link for link in unique_links}
            for fut in as_completed(futures):
                link, data = fut.result()
                # apply thresholds
                if (
                    mx_dr <= data["dr"] <= mn_dr
                    and data["traffic"] >= target_traffic
                    and data["ranking_keywords"] >= target_ranking
                    and data["traffic_percent"] >= target_precentage_traffic
                ):
                    passed.append({"link": link, **data})

        return {"output": passed}
