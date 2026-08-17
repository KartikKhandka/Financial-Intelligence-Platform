import sqlite3

import requests
from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter()

@router.get("/{ticker}/documents")
def get_company_documents(ticker: str, db: sqlite3.Connection = Depends(get_db)):

    query = "SELECT year, annual_report as url FROM documents WHERE company_id = ?"
    cursor = db.execute(query, (ticker,))
    docs = [dict(row) for row in cursor.fetchall()]

    if not docs:
        raise HTTPException(
            status_code=404, detail="No documents found for this company"
        )

    for doc in docs:
        url = doc["url"]
        is_valid = False
        if url:
            try:

                resp = requests.head(url, timeout=3)
                if resp.status_code < 400:
                    is_valid = True
            except:
                pass
        doc["is_url_valid"] = is_valid

    return docs