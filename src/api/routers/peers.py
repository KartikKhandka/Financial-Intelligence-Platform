import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter()

@router.get("/{group_name}")
def get_peer_group(group_name: str, db: sqlite3.Connection = Depends(get_db)):

    query = """
        SELECT *
        FROM peer_percentiles
        WHERE peer_group_name = ?
    """
    cursor = db.execute(query, (group_name,))
    data = [dict(row) for row in cursor.fetchall()]

    if not data:
        raise HTTPException(status_code=404, detail="Peer group not found")

    companies = {}
    for row in data:
        cid = row["company_id"]
        if cid not in companies:
            companies[cid] = {"company_id": cid, "metrics": {}}
        companies[cid]["metrics"][row["metric"]] = {
            "value": row["value"],
            "percentile_rank": row["percentile_rank"],
            "year": row["year"],
        }

    return list(companies.values())