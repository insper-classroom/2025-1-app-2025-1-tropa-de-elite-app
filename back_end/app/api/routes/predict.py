from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from tempfile import TemporaryDirectory
import joblib
import pandas as pd
from app.config import MODEL_PATH, THRESHOLD, BASE_DIR
from scripts.feature_pipeline import process_pipeline

router = APIRouter()

MODELS_DIR = BASE_DIR / "models"
PROCESSED_PATH = BASE_DIR / "data" / "processed_data.parquet"

# Utilitário para carregar modelo
def load_model(nome, variante, versao):
    model_path = MODELS_DIR / variante / f"{variante}_{versao}.joblib"
    if not model_path.exists():
        raise HTTPException(404, f"Modelo não encontrado: {model_path}")
    return joblib.load(model_path)

@router.post("/")
async def predict(
    payers_file: bytes,
    sellers_file: bytes,
    transactions_file: bytes,
    nome: str = Query(...),
    variante: str = Query(...),
    versao: str = Query(...)
):
    with TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "payers.feather").write_bytes(payers_file)
        (tmp / "sellers.feather").write_bytes(sellers_file)
        (tmp / "transactions.feather").write_bytes(transactions_file)
        df = process_pipeline(tmp/"payers.feather", tmp/"sellers.feather", tmp/"transactions.feather")
    try:
        model = load_model(nome, variante, versao)
        X     = df[model.feature_names_in_]
        proba = model.predict_proba(X)[:,1]
        preds = (proba >= THRESHOLD).astype(int)
    except Exception as e:
        raise HTTPException(500, f"Erro no modelo: {e}")
    return {"predictions": preds.tolist(), "probabilities": proba.tolist(), "threshold": THRESHOLD}

@router.get("/predict_row")
def predict_row(
    nome: str = Query(...),
    variante: str = Query(...),
    versao: str = Query(...),
    row_index: int = Query(...)
):
    if not PROCESSED_PATH.exists():
        raise HTTPException(404, "Dados processados não encontrados")
    df = pd.read_parquet(PROCESSED_PATH)
    if row_index < 0 or row_index >= len(df):
        raise HTTPException(400, "Índice de linha inválido")
    row = df.iloc[[row_index]]  # Mantém DataFrame
    model = load_model(nome, variante, versao)
    X = row[model.feature_names_in_]
    proba = model.predict_proba(X)[:,1]
    pred = (proba >= THRESHOLD).astype(int)
    return {
        "row_index": row_index,
        "prediction": int(pred[0]),
        "probability": float(proba[0]),
        "features": X.to_dict(orient="records")[0]
    }

@router.get("/predict_all")
def predict_all(
    nome: str = Query(...),
    variante: str = Query(...),
    versao: str = Query(...)
):
    if not PROCESSED_PATH.exists():
        raise HTTPException(404, "Dados processados não encontrados")
    df = pd.read_parquet(PROCESSED_PATH)
    model = load_model(nome, variante, versao)
    X = df[model.feature_names_in_]
    proba = model.predict_proba(X)[:,1]
    preds = (proba >= THRESHOLD).astype(int)
    return {
        "predictions": preds.tolist(),
        "probabilities": proba.tolist(),
        "threshold": THRESHOLD
    }
