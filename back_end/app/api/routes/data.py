from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
from scripts.feature_pipeline import process_pipeline

router = APIRouter()
BASE_DIR      = Path(__file__).parent.parent.parent
UPLOAD_DIR    = BASE_DIR / "uploads";   UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR = BASE_DIR / "data";      PROCESSED_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_files(
    payers_file: UploadFile = File(...),
    seller_terminals_file: UploadFile = File(...),
    transactional_train_file: UploadFile = File(...)
):
    paths = {
        "payers": UPLOAD_DIR / "payers.feather",
        "seller_terminals": UPLOAD_DIR / "seller_terminals.feather",
        "transactional_train": UPLOAD_DIR / "transactional_train.feather",
    }
    try:
        for key, upload in [
            ("payers", payers_file),
            ("seller_terminals", seller_terminals_file),
            ("transactional_train", transactional_train_file)
        ]:
            dest = paths[key]
            with open(dest, "wb") as f:
                f.write(await upload.read())
    except Exception as e:
        raise HTTPException(500, f"Erro ao salvar: {e}")
    return {"message": "Arquivos recebidos", "paths": [str(p) for p in paths.values()]}

@router.post("/process")
def process_data():
    p = UPLOAD_DIR
    for name in ["payers.feather", "seller_terminals.feather", "transactional_train.feather"]:
        if not (p / name).exists():
            raise HTTPException(404, f"Falta arquivo upload: {name}")
    df = process_pipeline(
        p/"payers.feather", p/"seller_terminals.feather", p/"transactional_train.feather"
    )
    out = PROCESSED_DIR / "processed_data.parquet"
    df.to_parquet(out, index=False)
    # head dos dados
    head = df.head(5).to_dict(orient="records")
    # features extraídas
    features = list(df.columns)
    return {
        "message": "Processado",
        "output": str(out),
        "head": head,
        "features": features
    }

@router.get("/download_processed")
def download_processed():
    out = PROCESSED_DIR / "processed_data.parquet"
    if not out.exists():
        raise HTTPException(404, "Processado não encontrado")
    return FileResponse(out, media_type="application/octet-stream")

@router.get("/processed_rows")
def get_processed_rows():
    out = PROCESSED_DIR / "processed_data.parquet"
    if not out.exists():
        raise HTTPException(404, "Processado não encontrado")
    import pandas as pd
    df = pd.read_parquet(out)
    head = df.head(25).to_dict(orient="records")
    return {"rows": head, "columns": list(df.columns)}

@router.get("/search_rows")
def search_rows(q: str = Query("", alias="q")):
    out = PROCESSED_DIR / "processed_data.parquet"
    if not out.exists():
        raise HTTPException(404, "Processado não encontrado")
    import pandas as pd
    import re
    from datetime import datetime
    
    df = pd.read_parquet(out)
    
    # Parse the query to check for dates
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    dates = re.findall(date_pattern, q)
    
    if len(dates) >= 2:
        # If we have 2 dates, use them as range
        start_date, end_date = dates[:2]
        # Remove dates from the query
        search_term = q.replace(start_date, "").replace(end_date, "").strip()
        
        try:
            # Filter by date range
            mask = (
                (df["tx_datetime"].astype(str) >= start_date) &
                (df["tx_datetime"].astype(str) <= end_date)
            )
            
            # Additional filter by card_bin if search term exists
            if search_term:
                mask = mask & df["card_bin"].astype(str).str.contains(search_term, case=False, na=False)
                
            filtered = df[mask]
        except Exception as e:
            raise HTTPException(400, f"Erro ao filtrar por data: {e}")
            
    elif len(dates) == 1:
        # If we have 1 date, use as exact match
        date = dates[0]
        # Remove date from the query
        search_term = q.replace(date, "").strip()
        
        try:
            # Filter by exact date
            mask = df["tx_datetime"].astype(str).str.startswith(date)
            
            # Additional filter by card_bin if search term exists
            if search_term:
                mask = mask & df["card_bin"].astype(str).str.contains(search_term, case=False, na=False)
                
            filtered = df[mask]
        except Exception as e:
            raise HTTPException(400, f"Erro ao filtrar por data: {e}")
    elif q:
        # Regular search by card_bin or date string
        mask = (
            df["tx_datetime"].astype(str).str.contains(q, case=False, na=False) |
            df["card_bin"].astype(str).str.contains(q, case=False, na=False)
        )
        filtered = df[mask]
    else:
        filtered = df
        
    head = filtered.head(10).to_dict(orient="records")
    return {"rows": head, "columns": list(df.columns)}
