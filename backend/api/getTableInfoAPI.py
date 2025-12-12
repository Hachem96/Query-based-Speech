from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd

from backend.searchinDatabase import get_table_from_db

router = APIRouter()

class TableInfoRequest(BaseModel):
    tableName: str
    columnsName: List[str]

class TableInfoResponse(BaseModel):
    success: bool
    tableName: str
    data: List[Dict[str, Any]]  # each row is a dict


@router.post("/", response_model=TableInfoResponse)
async def get_table_info(request: TableInfoRequest):
    try:
        df = get_table_from_db(None,request.tableName, request.columnsName)

        # Convert DataFrame → list of dicts (table-like JSON)
        data = df.to_dict(orient="records")

        return TableInfoResponse(
            success=True,
            tableName=request.tableName,
            data=data
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching table info: {str(e)}"
        )
