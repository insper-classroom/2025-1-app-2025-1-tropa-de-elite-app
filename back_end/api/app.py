# api/app.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
import shutil
import uuid
import joblib
import boto3
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Table, MetaData
from datetime import datetime
from fastapi import FastAPI
from pathlib import Path
import os
from dotenv import load_dotenv

# Carrega o .env (procura automaticamente na raiz do projeto)
load_dotenv()

app = FastAPI(title="Fraud Prediction API")

# Agora você pode acessar:
S3_BUCKET    = os.getenv("S3_BUCKET")
S3_KEY_DATA  = os.getenv("S3_KEY_DATA")
MODEL_PATH   = Path(os.getenv("MODEL_PATH"))
DATABASE_URL = os.getenv("DATABASE_URL")
# -----------------------------------------------------------------------------
# 1) CONFIGURAÇÃO GERAL
# -----------------------------------------------------------------------------

app = FastAPI(title="Fraud Prediction (apenas transaction_id)")

# --- 1.1) variáveis S3 e Paths locais ---
S3_BUCKET       = "seu-bucket-aqui"  
S3_KEY_DATA     = "data_only_frauds-v2/data_only_frauds-v2.parquet"
TMP_DIR         = Path("/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_DATA_PATH = TMP_DIR / "data_only_frauds-v2.parquet"

# --- 1.2) caminho do seu modelo treinado (joblib) ---
MODEL_PATH = Path("/path/para/seu/dummy_model.joblib")
# ajuste conforme a localização real, ex:
# MODEL_PATH = Path("../model/dummy_model.joblib")

# --- 1.3) Configuração do banco de logs (opcional) ---
DATABASE_URL = "postgresql://neondb_owner:npg_3Ci2vZGmBofM@ep-morning-mouse-acjafuzl-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
prediction_logs = Table(
    "prediction_logs", metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("transaction_id", String, index=True),
    Column("timestamp", DateTime),
    Column("is_fraud", Boolean),
    Column("fraud_probability", Float),
)
metadata.create_all(bind=engine)

# --- 1.4) cliente S3 (boto3) ---
s3_client = boto3.client("s3")

def download_parquet_from_s3(bucket: str, key: str, local_path: Path):
    """
    Faz download do arquivo Parquet do S3 para o sistema de arquivos local (/tmp).
    Se falhar, lança um RuntimeError.
    """
    try:
        s3_client.download_file(bucket, key, str(local_path))
    except Exception as e:
        raise RuntimeError(f"Não foi possível baixar '{key}' do S3: {e}")

# -----------------------------------------------------------------------------
# 2) STARTUP: carregar modelo + dataset inteiro em memória
# -----------------------------------------------------------------------------

@app.on_event("startup")
def load_model_and_data():
    # 2.1) carregar modelo em memória
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Modelo não encontrado em {MODEL_PATH}")
    app.state.model = joblib.load(MODEL_PATH)

    # 2.2) baixar do S3 (se ainda não existir localmente)
    #      ou sempre sobrescrever (à sua escolha). Aqui sempre sobrescrevemos:
    if LOCAL_DATA_PATH.exists():
        LOCAL_DATA_PATH.unlink()
    try:
        download_parquet_from_s3(S3_BUCKET, S3_KEY_DATA, LOCAL_DATA_PATH)
    except RuntimeError as e:
        raise RuntimeError(f"Falha no startup ao baixar dataset: {e}")

    # 2.3) ler Parquet inteiro em memória
    try:
        df_all = pd.read_parquet(LOCAL_DATA_PATH)
    except Exception as e:
        raise RuntimeError(f"Falha ao ler Parquet '{LOCAL_DATA_PATH}': {e}")

    # 2.4) verificar coluna 'transaction_id' existe
    if "transaction_id" not in df_all.columns:
        raise RuntimeError("O Parquet data_only_frauds-v2 não contém 'transaction_id'. Ele é obrigatório.")
    app.state.df_all = df_all

    print("Startup concluído: modelo e data_only_frauds-v2 carregados em memória.")


# -----------------------------------------------------------------------------
# 3) ENDPOINT: recebe apenas lista de transaction_id e prediz
# -----------------------------------------------------------------------------

@app.post("/predict_only_transactions")
async def predict_only_transactions(
    file: UploadFile = File(
        ...,
        description="Um arquivo CSV (ou Parquet simples) contendo apenas uma coluna 'transaction_id'."
    )
):
    """
    1) Recebe um CSV (ou Parquet) com coluna 'transaction_id'
    2) Lê essa lista de IDs
    3) Filtra o DataFrame pré-carregado (app.state.df_all) para só esses IDs
    4) Extrai colunas de features (todas, exceto transaction_id e is_fraud se existir)
    5) Executa model.predict(...) e model.predict_proba(...)
    6) Retorna JSON com [{ transaction_id, approved, probability_of_fraud }, ...]
    """

    # --- 3.1) Salvar temporário em /tmp e ler como DataFrame ---
    ext = Path(file.filename).suffix.lower()
    temp_in = TMP_DIR / f"ids_{uuid.uuid4()}{ext}"
    try:
        with open(temp_in, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if ext in {".csv"}:
            df_ids = pd.read_csv(temp_in, dtype={"transaction_id": str})
        elif ext in {".parquet", ".feather"}:
            df_ids = pd.read_parquet(temp_in)
        else:
            temp_in.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="Formato inválido. Use CSV, Parquet ou Feather contendo apenas 'transaction_id'."
            )
    except HTTPException as he:
        raise he
    except Exception as e:
        if temp_in.exists():
            temp_in.unlink()
        raise HTTPException(status_code=500, detail=f"Não foi possível ler a lista de IDs: {e}")

    # apagar o temporário, pois não precisamos mais
    temp_in.unlink(missing_ok=True)

    # --- 3.2) Validar coluna 'transaction_id' existe e é texto ---
    if "transaction_id" not in df_ids.columns:
        raise HTTPException(status_code=400, detail="O arquivo de entrada deve ter coluna 'transaction_id'.")

    df_ids["transaction_id"] = df_ids["transaction_id"].astype(str)

    # --- 3.3) Filtrar o DataFrame pré-carregado para só os IDs solicitados ---
    df_all = app.state.df_all
    # Para aumentar a performance, podemos fazer um inner join por “transaction_id”:
    merged = df_all.merge(
        df_ids[["transaction_id"]].drop_duplicates(),
        on="transaction_id",
        how="inner"
    )
    if merged.empty:
        return JSONResponse(
            status_code=200,
            content={
                "message": "Nenhum transaction_id encontrado em data_only_frauds-v2",
                "count": 0,
                "results": []
            }
        )

    # --- 3.4) Preparar vetor de features para predição ---
    # Assumimos que em 'merged' estão:
    #   - coluna 'transaction_id'
    #   - possivelmente 'is_fraud' (não usaremos)
    #   - e TODAS as colunas de features que o seu modelo espera (por ex: tx_amount_log, tx_hour_of_day, card_age_days, …)
    #
    # Vamos extrair exatamente as colunas de features:
    cols_all = list(merged.columns)
    # remover coluna 'transaction_id' e 'is_fraud' se existir
    bad = {"transaction_id", "is_fraud"}
    feature_cols = [c for c in cols_all if c not in bad]
    if not feature_cols:
        raise HTTPException(
            status_code=500,
            detail="Não houve nenhuma coluna de features em data_only_frauds-v2 (além de 'transaction_id' ou 'is_fraud')."
        )

    X = merged[feature_cols].copy()

    # --- 3.5) Executar predição ---
    model = app.state.model
    try:
        y_pred = model.predict(X)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha em model.predict: {e}")

    # predict_proba pode não existir, então protegemos:
    if hasattr(model, "predict_proba"):
        try:
            y_prob = model.predict_proba(X)[:, 1].tolist()
        except Exception:
            # se der erro, preenche com zeros
            y_prob = [0.0] * len(X)
    else:
        y_prob = [0.0] * len(X)

    # --- 3.6) Montar resposta e gravar log no banco ---
    results = []
    with engine.connect() as conn:
        for i, row in merged.reset_index(drop=True).iterrows():
            tx_id = row["transaction_id"]
            is_fraud = int(y_pred[i])  # 1 → fraude, 0 → não fraude
            approved = True if is_fraud == 0 else False
            prob = float(y_prob[i])

            # Inserir no prediction_logs (NeonDB)
            conn.execute(
                prediction_logs.insert().values(
                    transaction_id=tx_id,
                    timestamp=datetime.utcnow(),
                    is_fraud=bool(is_fraud),
                    fraud_probability=prob
                )
            )

            results.append({
                "transaction_id": tx_id,
                "approved": approved,
                "probability_of_fraud": prob
            })
        conn.commit()

    return {
        "message": f"Predição concluída: {len(results)} registros",
        "count": len(results),
        "results": results
    }
