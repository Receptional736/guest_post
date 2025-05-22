import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn
import datetime
from typing import Iterable, List
import requests

from SerpSearchPy import SerpSearcher
from Ahref_metrics import AhrefsMetrics
#----------------------------------------------CONF--------------------------------------------
load_dotenv()

app = FastAPI(
    title="SERP Searcher API",
    description="Expose SerpSearcher via REST",
    version="1.0.0",
)

security = HTTPBearer()
API_BEARER_TOKEN = os.getenv("SERP_TOKEN_AUTH")


class SearchRequest(BaseModel):


    keywords: str
    country: Optional[str] = ""
    acceptable_tlds: Optional[str] = ""

class AhrefRequest(BaseModel):
    country: Optional[str] = "gb"
    max_dr: Optional[str] = "0"
    min_dr: Optional[str] = "100"
    traffic: Optional[str] = "0"
    ranking: Optional[str] = "0"
    keywords: str
    acceptable_tlds: Optional[str] = "all"
    pres_traffic: Optional[str] = "0.0"

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:

    if credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )




#-----------------------------------URLS-----------------------------------------

@app.post("/serpsearch", dependencies=[Depends(verify_token)])
async def search(request: SearchRequest):

    try:
        searcher = SerpSearcher(
            keywords=request.keywords,
            country=request.country,
            acceptable_tlds=request.acceptable_tlds,
        )
        return searcher.search()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        ) from exc



@app.post("/ahrefmetric", dependencies=[Depends(verify_token)])
async def search(request: AhrefRequest):

    try:
     
        date = datetime.date.today().isoformat()

        

        searcher = SerpSearcher(
            keywords=request.keywords,
            country=request.country,
            acceptable_tlds=request.acceptable_tlds,
        )
        domains =  searcher.search()
        links = domains['output']
        client = AhrefsMetrics(request.country,date)
        max_dr, min_dr, traffic,ranking, pres_traffic = request.max_dr, request.min_dr, request.traffic, request.ranking, request.pres_traffic


        max_dr = float(request.max_dr) if request.max_dr else 0.0
        min_dr = float(request.min_dr) if request.min_dr else 100.0
        traffic = int(request.traffic or 0)
        ranking = int(request.ranking or 0)
        pres_traffic = float(request.pres_traffic or 0.0)

        try:
            result = client.filter_links(
                links,
                mx_dr=max_dr,
                mn_dr=min_dr,
                target_traffic=traffic,
                target_ranking=ranking,
                target_precentage_traffic=pres_traffic,
            )


            return result
        
        except Exception as e:
            print(e)
            result = {'output': [{'link': ''}, {'dr': ''}, {'traffic': ''}, {'traffic_percent': ''}, {'ranking_keywords': ''},{'target_precentage_traffic':''}]}
            return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        ) from exc





#-----------------------------------main app-------------------------------------------


if __name__ == "__main__":
    

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
