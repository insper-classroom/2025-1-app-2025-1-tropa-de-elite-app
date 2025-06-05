from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import joblib
import boto3
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from datetime import datetime
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import List
import os
import io
import uuid

# ─── Carrega .env ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
if (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env")
elif (BASE_DIR.parent / ".env").exists():
    load_dotenv(BASE_DIR.parent / ".env")
else:
    load_dotenv()

# ─── Vars de ambiente ─────────────────────────────────────────────────────────
S3_BUCKET      = os.getenv("S3_BUCKET")
S3_KEY_DATA    = os.getenv("S3_KEY_DATA")
S3_KEY_MODEL   = os.getenv("S3_KEY_MODEL")
S3_KEY_PAYERS  = os.getenv("S3_KEY_PAYERS")
S3_KEY_SELLERS = os.getenv("S3_KEY_SELLERS")
DATABASE_URL   = os.getenv("DATABASE_URL")

for v in ("S3_BUCKET", "S3_KEY_DATA", "S3_KEY_MODEL", "S3_KEY_PAYERS", "S3_KEY_SELLERS", "DATABASE_URL"):
    if not os.getenv(v):
        raise RuntimeError(f"Variável {v} não está definida.")

TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ─── Configuração do banco de logs (SQLAlchemy) ───────────────────────────────
# from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Table, MetaData
# from sqlalchemy.exc import SQLAlchemyError

# engine = create_engine(DATABASE_URL, echo=False)
# metadata = MetaData()

# prediction_logs = Table(
#     "prediction_logs", metadata,
#     Column("id", Integer, primary_key=True, autoincrement=True),
#     Column("transaction_id", String, index=True),
#     Column("timestamp", DateTime),
#     Column("is_fraud", Boolean),
#     Column("fraud_probability", Float),
# )
# # metadata.create_all(bind=engine)

# ─── Cliente S3 ───────────────────────────────────────────────────────────────
s3_client = boto3.client("s3")

def download_from_s3(bucket: str, key: str, local_path: Path) -> None:
    try:
        if local_path.exists():
            head = s3_client.head_object(Bucket=bucket, Key=key)
            size_remoto = head["ContentLength"]
            if local_path.stat().st_size == size_remoto:
                return
        local_path.parent.mkdir(parents=True, exist_ok=True)
        s3_client.download_file(bucket, key, str(local_path))
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar '{key}' do bucket '{bucket}': {e}")

# ─── Pydantic Models e estado global ──────────────────────────────────────────
class NewTransactionInput(BaseModel):
    card_id: str = Field(..., example="abcd1234")
    terminal_id: str = Field(..., example="term5678")
    tx_datetime: datetime = Field(..., example="2025-06-05T14:23:00Z")
    tx_amount: float = Field(..., example=123.45)

class PredictionResult(BaseModel):
    transaction_id: str
    approved: bool
    probability_of_fraud: float

class AppState:
    model = None
    df_merged_base = None
    df_payers = None
    df_sellers = None

state = AppState()

# ─── Calcula features para cada linha ──────────────────────────────────────────
def compute_features_for_row(row, df_card_prev, df_term_prev):
    f = {}
    dt = row["tx_datetime"]

    # 1) numéricas básicas
    f["tx_amount"] = float(row["tx_amount"])
    f["tx_hour_of_day"] = dt.hour
    f["tx_dayofweek"] = dt.weekday()

    # 2) card_age_days
    if pd.notna(row["card_first_transaction"]):
        f["card_age_days"] = float((dt - row["card_first_transaction"]).days)
    else:
        f["card_age_days"] = 0.0

    # 3) tx_time_diff_prev
    if not df_card_prev.empty:
        last_time = df_card_prev["tx_datetime"].max()
        diff_s = (dt - last_time).total_seconds()
        f["tx_time_diff_prev"] = float(np.log10(diff_s + 1))
    else:
        f["tx_time_diff_prev"] = 0.0

    # 4) amount_card_norm_pdf (placeholder: 0.5)
    f["amount_card_norm_pdf"] = 0.5

    # 5) terminal_age_days
    if pd.notna(row["terminal_operation_start"]):
        f["terminal_age_days"] = float((dt - row["terminal_operation_start"]).days)
    else:
        f["terminal_age_days"] = 0.0

    # 6) terminal_card_reuse_ratio_prior (placeholder: 0.0)
    f["terminal_card_reuse_ratio_prior"] = 0.0

    # 7) shared_terminal_with_frauds_prior
    df_term_frauds = df_term_prev[
        (df_term_prev["is_fraud"] == 1) &
        (df_term_prev["tx_fraud_report_date"].notna()) &
        (df_term_prev["tx_fraud_report_date"] < dt)
    ]
    f["shared_terminal_with_frauds_prior"] = float(df_term_frauds["card_id"].nunique()) if not df_term_frauds.empty else 0.0

    # 8) card_fraud_count_last_1d, card_fraud_count_last_7d
    df_card_frauds = df_card_prev[df_card_prev["is_fraud"] == 1]
    if not df_card_frauds.empty:
        one_day_ago = dt - pd.Timedelta(days=1)
        seven_days_ago = dt - pd.Timedelta(days=7)
        f["card_fraud_count_last_1d"] = float(
            df_card_frauds[df_card_frauds["tx_fraud_report_date"] >= one_day_ago].shape[0]
        )
        f["card_fraud_count_last_7d"] = float(
            df_card_frauds[df_card_frauds["tx_fraud_report_date"] >= seven_days_ago].shape[0]
        )
    else:
        f["card_fraud_count_last_1d"] = 0.0
        f["card_fraud_count_last_7d"] = 0.0

    # 9) card_nonfraud_count_last_1d, card_nonfraud_count_last_7d
    df_card_nonfrauds = df_card_prev[df_card_prev["is_fraud"] == 0]
    if not df_card_nonfrauds.empty:
        one_day_ago = dt - pd.Timedelta(days=1)
        seven_days_ago = dt - pd.Timedelta(days=7)
        f["card_nonfraud_count_last_1d"] = float(
            df_card_nonfrauds[df_card_nonfrauds["tx_datetime"] >= one_day_ago].shape[0]
        )
        f["card_nonfraud_count_last_7d"] = float(
            df_card_nonfrauds[df_card_nonfrauds["tx_datetime"] >= seven_days_ago].shape[0]
        )
    else:
        f["card_nonfraud_count_last_1d"] = 0.0
        f["card_nonfraud_count_last_7d"] = 0.0

    # 10) amount_terminal_norm_pdf (placeholder: 0.5)
    f["amount_terminal_norm_pdf"] = 0.5

    # 11) avg_speed_between_txs (placeholder: 0.0)
    f["avg_speed_between_txs"] = 0.0

    # 12) cardbin_fraud_count_last_30d
    if pd.notna(row["card_bin"]):
        my_bin = row["card_bin"]
        df_bin_prev = df_card_prev[
            (df_card_prev["card_bin"] == my_bin) &
            (df_card_prev["tx_fraud_report_date"].notna()) &
            (df_card_prev["tx_datetime"] < dt) &
            (df_card_prev["tx_datetime"] >= dt - pd.Timedelta(days=30))
        ]
        f["cardbin_fraud_count_last_30d"] = float(df_bin_prev.shape[0])
    else:
        f["cardbin_fraud_count_last_30d"] = 0.0

    # ─── CATEGÓRICAS ──────────────────────────────────────────────────────────
    f["card_bin"] = row["card_bin"] if pd.notna(row["card_bin"]) else "UNKNOWN"
    f["terminal_soft_descriptor"] = row["terminal_soft_descriptor"] if pd.notna(row["terminal_soft_descriptor"]) else "UNKNOWN"
    lat = row.get("latitude", np.nan)
    if pd.notna(lat):
        if lat > -10:
            f["regiao"] = "Norte"
        elif lat > -20:
            f["regiao"] = "Centro-Oeste"
        else:
            f["regiao"] = "Sudeste"
    else:
        f["regiao"] = "UNKNOWN"

    return f

# def log_prediction_to_db(transaction_id: str, timestamp: datetime, is_fraud: bool, fraud_prob: float):
#     ins = prediction_logs.insert().values(
#         transaction_id=transaction_id,
#         timestamp=timestamp,
#         is_fraud=is_fraud,
#         fraud_probability=fraud_prob
#     )
#     try:
#         with engine.begin() as conn:
#             conn.execute(ins)
#     except SQLAlchemyError as e:
#         print(f"[WARN] Falha ao gravar log no BD: {e}")

# ─── Ciclo de vida (startup) ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) Baixa e carrega Parquet das 5 M preprocessadas (features-only)
    local_data = TMP_DIR / Path(S3_KEY_DATA).name
    download_from_s3(S3_BUCKET, S3_KEY_DATA, local_data)
    df_5m = pd.read_parquet(local_data)
    state.df_merged_base = df_5m
    print(f"[INFO] Carregadas 5 M preprocessadas em memória ({len(df_5m)} linhas).")

    # 2) Baixa e carrega modelo joblib
    local_model = TMP_DIR / Path(S3_KEY_MODEL).name
    download_from_s3(S3_BUCKET, S3_KEY_MODEL, local_model)
    state.model = joblib.load(local_model)
    print(f"[INFO] Pipeline XGBoost carregado de: {local_model}")

    # 3) Baixa e carrega payers e sellers (Feather)
    local_payers  = TMP_DIR / Path(S3_KEY_PAYERS).name
    local_sellers = TMP_DIR / Path(S3_KEY_SELLERS).name
    download_from_s3(S3_BUCKET, S3_KEY_PAYERS, local_payers)
    download_from_s3(S3_BUCKET, S3_KEY_SELLERS, local_sellers)

    temp_payers = pd.read_feather(local_payers)
    temp_sellers = pd.read_feather(local_sellers)

    # Ajuste de payers: usar card_hash como card_id, se existir
    if "card_hash" in temp_payers.columns:
        temp_payers["card_id"] = temp_payers["card_hash"]
    elif "card_id" in temp_payers.columns:
        temp_payers["card_id"] = temp_payers["card_id"]
    else:
        raise RuntimeError("Nenhuma coluna 'card_hash' nem 'card_id' em payers.feather")
    state.df_payers = temp_payers[["card_id", "card_bin", "card_first_transaction"]]

    # Ajuste de sellers: apenas solicita terminal_id
    if "terminal_id" not in temp_sellers.columns:
        raise RuntimeError("'terminal_id' não encontrado em sellers.feather")

# +   # converter terminal_operation_start para datetime
# +   if "terminal_operation_start" in temp_sellers.columns:
# +       temp_sellers["terminal_operation_start"] = pd.to_datetime(
# +           temp_sellers["terminal_operation_start"], errors="coerce"
# +       )

    state.df_sellers = temp_sellers[[
        "terminal_id","latitude","longitude","terminal_operation_start","terminal_soft_descriptor"
    ]]

    print("[INFO] Payers e Sellers carregados em memória.")

    # Ajuste de sellers: apenas solicita terminal_id
    if "terminal_id" not in temp_sellers.columns:
        raise RuntimeError("'terminal_id' não encontrado em sellers.feather")
    state.df_sellers = temp_sellers[[
        "terminal_id", "latitude", "longitude", "terminal_operation_start", "terminal_soft_descriptor"
    ]]

    print("[INFO] Payers e Sellers carregados em memória.")
    yield
    # (opcional: limpar TMP_DIR)

# ─── FastAPI ────────────────────────────────────────────────────────────────
app = FastAPI(title="Fraud Detection API", version="1.0", lifespan=lifespan)

# ─── Colunas do pipeline ─────────────────────────────────────────────────────
CAT_COLS = ["regiao"]
NUM_COLS = [
    "tx_amount", "tx_hour_of_day", "tx_dayofweek", "card_age_days", "tx_time_diff_prev",
    "amount_card_norm_pdf", "terminal_age_days", "terminal_card_reuse_ratio_prior",
    "shared_terminal_with_frauds_prior", "card_fraud_count_last_1d",
    "card_nonfraud_count_last_1d", "card_fraud_count_last_7d", "card_nonfraud_count_last_7d",
    "amount_terminal_norm_pdf", "avg_speed_between_txs", "cardbin_fraud_count_last_30d"
]
FEATURE_COLUMNS = CAT_COLS + NUM_COLS

# ─── Endpoint /predict_batch_file ────────────────────────────────────────────
@app.post("/predict_batch_file", response_model=List[PredictionResult])
async def predict_from_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".feather"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .feather")

    try:
        content = await file.read()
        df_new_all = pd.read_feather(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao ler .feather: {e}")

    # Verifica colunas mínimas
    required = {"transaction_id", "tx_datetime", "tx_amount", "card_id", "terminal_id"}
    missing = required - set(df_new_all.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Colunas obrigatórias ausentes: {missing}")

    # Converte tipos e extrai tx_amount→log1p, hora, dia
    df_new_all["tx_datetime"] = pd.to_datetime(df_new_all["tx_datetime"], errors="coerce")
    # Certifique-se que tx_amount é float antes do log1p para evitar erro se já for logaritmizado
    if df_new_all["tx_amount"].dtype != 'float64' and df_new_all["tx_amount"].dtype != 'float32':
        df_new_all["tx_amount"] = df_new_all["tx_amount"].astype(float)
    # Apenas aplicar log1p se não for já pequeno (indicativo de já ser log)
    # Esta é uma heurística, idealmente você saberia o estado da coluna.
    if df_new_all["tx_amount"].max() > 15: # Um valor arbitrário, ajuste conforme necessário
        df_new_all["tx_amount"] = np.log1p(df_new_all["tx_amount"])


    df_new_all["tx_hour_of_day"] = df_new_all["tx_datetime"].dt.hour
    df_new_all["tx_dayofweek"] = df_new_all["tx_datetime"].dt.weekday

    # Merge com payers e sellers (colunas estáticas)
    df_new_all = df_new_all.merge(
        state.df_payers, on="card_id", how="left"
    ).merge(
        state.df_sellers, on="terminal_id", how="left"
    )

    # Garanta que as colunas de data para cálculo de age sejam datetime
    if "card_first_transaction" in df_new_all.columns:
        df_new_all["card_first_transaction"] = pd.to_datetime(
            df_new_all["card_first_transaction"], errors="coerce"
        )
    if "terminal_operation_start" in df_new_all.columns:
        df_new_all["terminal_operation_start"] = pd.to_datetime(
            df_new_all["terminal_operation_start"], errors="coerce"
        )


    total = len(df_new_all)
    batch_size = 100 # Você pode ajustar este tamanho
    results: List[PredictionResult] = []

    for offset in range(0, total, batch_size):
        chunk = df_new_all.iloc[offset: offset + batch_size].copy()

        # Filtra histórico para este pedaço
        cards_chunk = chunk["card_id"].unique().tolist()
        terms_chunk = chunk["terminal_id"].unique().tolist()
        max_dt_chunk = chunk["tx_datetime"].max() # Usar max_dt do chunk atual

        # Filtra histórico base apenas uma vez se possível, ou otimiza
        df_hist_cards = state.df_merged_base.loc[
            (state.df_merged_base["card_id"].isin(cards_chunk)) &
            (state.df_merged_base["tx_datetime"] < max_dt_chunk) # Usar max_dt do chunk
        ]
        df_hist_terms = state.df_merged_base.loc[
            (state.df_merged_base["terminal_id"].isin(terms_chunk)) &
            (state.df_merged_base["tx_datetime"] < max_dt_chunk) # Usar max_dt do chunk
        ]

        features_list = []
        for idx, row in chunk.iterrows():
            # Filtragem mais específica do histórico para a linha atual
            df_card_prev_row = df_hist_cards[
                (df_hist_cards["card_id"] == row["card_id"]) &
                (df_hist_cards["tx_datetime"] < row["tx_datetime"]) # Garante que são transações ANTERIORES à atual
            ]
            df_term_prev_row = df_hist_terms[
                (df_hist_terms["terminal_id"] == row["terminal_id"]) &
                (df_hist_terms["tx_datetime"] < row["tx_datetime"]) # Garante que são transações ANTERIORES à atual
            ]
            feat = compute_features_for_row(row, df_card_prev_row, df_term_prev_row)
            features_list.append(feat)

        df_feat = pd.DataFrame(features_list, columns=FEATURE_COLUMNS) # df_feat é criado AQUI

        # ----- INÍCIO DA DEPURAÇÃO MOVIDO PARA CÁ -----
        # print(f"--- DEBUG API: predict_from_file (Chunk Offset: {offset}) ---")
        # nan_summary = df_feat.isnull().sum()
        # cols_with_nan = nan_summary[nan_summary > 0]
        # if not cols_with_nan.empty:
        #     print("COLUNAS COM NaNs EM df_feat ANTES DE predict_proba:")
        #     for col_name, nan_count in cols_with_nan.items():
        #         print(f"  - Coluna '{col_name}': {nan_count} NaNs")
        #         # Opcional: mostrar alguns valores da coluna com NaN
        #         # print(df_feat[df_feat[col_name].isnull()][col_name].head())
        # else:
        #     print("NENHUMA COLUNA COM NaNs detectada em df_feat antes de predict_proba.")

        # print("Resumo dos tipos de dados em df_feat:")
        # print(df_feat.dtypes)
        # print(f"--- FIM DEBUG API (Chunk Offset: {offset}) ---")
        # ----- FIM DA DEPURAÇÃO -----

        # Tratamento de NaNs ANTES de predict_proba, se necessário (exemplo genérico)
        # Seu pipeline já deve ter tratamento de NaN, mas se o erro persistir aqui,
        # isso pode ser um ponto para intervenção manual ou para entender por que
        # o pipeline não está lidando com eles.
        # df_feat[NUM_COLS] = df_feat[NUM_COLS].fillna(0) # Exemplo, ajuste conforme sua estratégia
        # df_feat[CAT_COLS] = df_feat[CAT_COLS].fillna("UNKNOWN") # Exemplo

        # Predição com threshold otimizado
        try:
            probs = state.model.predict_proba(df_feat)[:, 1]
        except ValueError as e:
            print(f"ERRO durante predict_proba no chunk offset {offset}: {e}")
            print("Detalhes de df_feat que causou o erro:")
            for col in df_feat.columns:
                if df_feat[col].isnull().any():
                    print(f"Coluna '{col}' contém NaNs: {df_feat[col].isnull().sum()} ocorrências.")
                    print(f"Valores únicos (com NaNs) em '{col}':\n{df_feat[col].value_counts(dropna=False).head(5)}")
            raise # Re-levanta a exceção para parar e analisar
            
        y_pred_arr = (probs >= 0.804907749976376).astype(int)
        y_prob_arr = probs

        tx_ids = chunk["transaction_id"].astype(str).tolist()
        for i, txid in enumerate(tx_ids):
            label = bool(int(y_pred_arr[i]))
            prob = float(y_prob_arr[i])
            # log_prediction_to_db(...)
            results.append(PredictionResult(
                transaction_id=txid,
                approved=(not label),
                probability_of_fraud=prob
            ))

    return JSONResponse(content=[r.model_dump() for r in results]) # Usar model_dump() para Pydantic v2+

# ─── Endpoint /predict_transaction ───────────────────────────────────────────
@app.post("/predict_transaction", response_model=PredictionResult)
async def predict_transaction(new_tx: NewTransactionInput):
    # 1) Gera um UUID para esta transação
    generated_tx_id = str(uuid.uuid4())

    # 2) Monta DataFrame mínimo para calcular features
    row = {
        "transaction_id": generated_tx_id,
        "card_id": new_tx.card_id,
        "terminal_id": new_tx.terminal_id,
        "tx_datetime": new_tx.tx_datetime,
        "tx_amount": np.log1p(new_tx.tx_amount),
    }
    df_row = pd.DataFrame([row])

    # 3) Merge com payers e sellers
    df_row = df_row.merge(
        state.df_payers, on="card_id", how="left"
    ).merge(
        state.df_sellers, on="terminal_id", how="left"
    )

    # 4) Filtra histórico para este cartão e terminal
    df_hist_cards = state.df_merged_base.loc[
        (state.df_merged_base["card_id"] == new_tx.card_id) &
        (state.df_merged_base["tx_datetime"] < new_tx.tx_datetime)
    ]
    df_hist_terms = state.df_merged_base.loc[
        (state.df_merged_base["terminal_id"] == new_tx.terminal_id) &
        (state.df_merged_base["tx_datetime"] < new_tx.tx_datetime)
    ]

    # 5) Calcula as features
    features = compute_features_for_row(df_row.iloc[0], df_hist_cards, df_hist_terms)
    df_feat = pd.DataFrame([features], columns=FEATURE_COLUMNS)

    df_feat[NUM_COLS] = df_feat[NUM_COLS].fillna(0)

    assert not df_feat["shared_terminal_with_frauds_prior"].isna().any(), \
    "Ainda existem NaN em shared_terminal_with_frauds_prior!"

    # 6) Predição usando o modelo
    probs = state.model.predict_proba(df_feat)[:, 1]
    prob = float(probs[0])
    label = bool(int(prob >= 0.804907749976376))

    # 7) Log no banco (com UUID gerado)
    # log_prediction_to_db(
    #     transaction_id=generated_tx_id,
    #     timestamp=new_tx.tx_datetime,
    #     is_fraud=label,
    #     fraud_prob=prob
    # )

    # 8) Retorna resultado
    return PredictionResult(
        transaction_id=generated_tx_id,
        approved=(not label),
        probability_of_fraud=prob
    )