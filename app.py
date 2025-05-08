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
    country: str 
    acceptable_tlds: Optional[List[str]] 

class AhrefRequest(BaseModel):
    country: str
    dr: int
    traffic: int
    ranking: int
    keywords: str
    acceptable_tlds: Optional[List[str]] 

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
            acceptable_tlds=request.acceptable_tlds or [],
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
            acceptable_tlds=request.acceptable_tlds or [],
        )
        domains =  searcher.search()
        links = domains['output']
        client = AhrefsMetrics(request.country,date)
        result = client.filter_links(links, target_dr=request.dr, 
                                     target_traffic=request.traffic,target_ranking=request.ranking)


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
