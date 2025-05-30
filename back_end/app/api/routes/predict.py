from fastapi import APIRouter, HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
import joblib
import pandas as pd
from app.config import MODEL_PATH, THRESHOLD
from scripts.feature_pipeline import process_pipeline

router = APIRouter()
model = joblib.load(MODEL_PATH)

@router.post("/")
async def predict(
    payers_file: bytes,
    sellers_file: bytes,
    transactions_file: bytes
):
    with TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "payers.feather").write_bytes(payers_file)
        (tmp / "sellers.feather").write_bytes(sellers_file)
        (tmp / "transactions.feather").write_bytes(transactions_file)
        df = process_pipeline(tmp/"payers.feather", tmp/"sellers.feather", tmp/"transactions.feather")
    try:
        X     = df[model.feature_names_in_]
        proba = model.predict_proba(X)[:,1]
        preds = (proba >= THRESHOLD).astype(int)
    except Exception as e:
        raise HTTPException(500, f"Erro no modelo: {e}")
    return {"predictions": preds.tolist(), "probabilities": proba.tolist(), "threshold": THRESHOLD}
