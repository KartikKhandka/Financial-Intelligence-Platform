import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.api.routers.companies import router as companies_router
from src.api.routers.documents import router as documents_router
from src.api.routers.health import router as health_router
from src.api.routers.peers import router as peers_router
from src.api.routers.portfolio import router as portfolio_router
from src.api.routers.screener import router as screener_router
from src.api.routers.sectors import router as sectors_router
from src.api.routers.valuation import router as valuation_router

app = FastAPI(title="Nifty 100 Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}ms"
    logger.info(f"{request.method} {request.url.path} - {formatted_process_time}")
    return response

app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(companies_router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(screener_router, prefix="/api/v1/screener", tags=["Screener"])
app.include_router(sectors_router, prefix="/api/v1/sectors", tags=["Sectors"])
app.include_router(peers_router, prefix="/api/v1/peers", tags=["Peers"])
app.include_router(valuation_router, prefix="/api/v1/market-cap", tags=["Valuation"])
app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(documents_router, prefix="/api/v1/companies", tags=["Documents"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)