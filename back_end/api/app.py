from fastapi import FastAPI, UploadFile, File, HTTPException,Query
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path
import pandas as pd
import uuid
import os
import sys
import joblib
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional
from sqlalchemy import delete

# Importa a função de pipeline do preprocess.py
sys.path.append(str(Path(__file__).parent / "scripts"))
from scripts.preprocess import process_pipeline

app = FastAPI(title="Fraud Detection API")

# Configuração de diretórios e arquivos
UPLOAD_DIR = Path("/tmp/uploads")
FEATURES_PATH = Path("/tmp/features.parquet")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = Path("model/sem_desacordo_v1.0.0.joblib")

# Configuração da conexão com o banco de dados
DATABASE_URL = "postgresql://neondb_owner:npg_3Ci2vZGmBofM@ep-morning-mouse-acjafuzl-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definição da tabela para logs de predição
metadata = MetaData()
prediction_logs = Table(
    "prediction_logs", 
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("transaction_id", String, index=True),
    Column("timestamp", DateTime),
    Column("is_fraud", Boolean),
    Column("tx_amount", Float),
    Column("fraud_probability", Float),
)

# Cria tabela se não existir
metadata.create_all(bind=engine)

# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()





@app.post("/upload-and-merge")
async def upload_and_merge(
    payers: UploadFile = File(...),
    sellers: UploadFile = File(...),
    transactions: UploadFile = File(...)
):
    """
    Upload e merge dos arquivos de payers, sellers e transactions.
    Gera um dataset unificado que será usado nas predições.
    Esta etapa precisa ser executada apenas uma vez antes das predições.
    """
    try:
        # 1. Salva arquivos temporariamente
        payers_path = UPLOAD_DIR / f"payers_{uuid.uuid4()}.feather"
        sellers_path = UPLOAD_DIR / f"sellers_{uuid.uuid4()}.feather"
        transactions_path = UPLOAD_DIR / f"transactions_{uuid.uuid4()}.feather"
        
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        for file, path in zip([payers, sellers, transactions], [payers_path, sellers_path, transactions_path]):
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # 2. Processa os dados e gera features
        print("Processando dados e gerando dataset unificado...")
        df_features = process_pipeline(payers_path, sellers_path, transactions_path)
        
        # 3. Salva o dataset processado para uso futuro
        FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
        df_features.to_parquet(FEATURES_PATH, index=False)
        
        # 4. Limpa arquivos temporários
        payers_path.unlink(missing_ok=True)
        sellers_path.unlink(missing_ok=True)
        transactions_path.unlink(missing_ok=True)
        
        # 5. Retorna estatísticas do dataset
        stats = {
            "total_transactions": len(df_features),
            "features_count": len(df_features.columns),
            "date_range": {
                "min": df_features['tx_datetime'].min().isoformat() if 'tx_datetime' in df_features else None,
                "max": df_features['tx_datetime'].max().isoformat() if 'tx_datetime' in df_features else None
            },
            "amount_stats": {
                "min": float(df_features['tx_amount'].min()) if 'tx_amount' in df_features else None,
                "max": float(df_features['tx_amount'].max()) if 'tx_amount' in df_features else None,
                "mean": float(df_features['tx_amount'].mean()) if 'tx_amount' in df_features else None
            },
            "features_path": str(FEATURES_PATH)
        }

        return {
            "message": "Dataset unificado gerado com sucesso!",
            "dataset_stats": stats
        }
    except Exception as e:
        # Tenta limpar arquivos em caso de erro
        try:
            payers_path.unlink(missing_ok=True)
            sellers_path.unlink(missing_ok=True)
            transactions_path.unlink(missing_ok=True)
        except:
            pass
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro durante o upload e merge: {str(e)}"
        )
    

@app.post("/predict-from-merged")
def predict_from_merged(
    # Filtros
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    transaction_id: Optional[str] = Query(None, description="ID específico da transação"),
    bin_number: Optional[str] = Query(None, description="BIN (primeiros 6 dígitos do cartão)"),
    min_amount: Optional[float] = Query(None, description="Valor mínimo da transação"),
    max_amount: Optional[float] = Query(None, description="Valor máximo da transação"),
    # Paginação
    page: int = Query(1, ge=1, description="Página a processar"),
    page_size: int = Query(1000, ge=10, le=10000, description="Transações por página"),
    # Opção para limpar logs
    clear_previous_logs: bool = Query(True, description="Limpar logs anteriores antes de inserir novos")
):
    """
    Faz predições usando o dataset já mergeado.
    Suporta filtragem e paginação para processar subconjuntos dos dados.
    Pode ser chamada múltiplas vezes com diferentes parâmetros.
    """
    try:
        # 1. Verifica se o dataset mergeado existe
        if not FEATURES_PATH.exists():
            raise HTTPException(
                status_code=400, 
                detail="Dataset unificado não encontrado. Execute primeiro o endpoint /upload-and-merge."
            )
            
        # 2. Carrega o dataset
        print("Carregando dataset unificado...")
        df_features = pd.read_parquet(FEATURES_PATH)
        
        # 3. Aplica filtros
        print("Aplicando filtros...")
        filtered_df = df_features.copy()
        
        # Filtros de data
        if start_date and 'tx_datetime' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['tx_datetime'] >= pd.to_datetime(start_date)]
            
        if end_date and 'tx_datetime' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['tx_datetime'] <= pd.to_datetime(end_date)]
        
        # Filtro por ID da transação
        if transaction_id and 'transaction_id' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['transaction_id'].str.contains(transaction_id, na=False)]
        
        # Filtro por BIN
        if bin_number and 'transaction_id' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['transaction_id'].str.startswith(bin_number, na=False)]
        
        # Filtros de valor
        if min_amount is not None and 'tx_amount' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['tx_amount'] >= min_amount]
            
        if max_amount is not None and 'tx_amount' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['tx_amount'] <= max_amount]
        
        # 4. Aplicar paginação no conjunto filtrado
        total_records = len(filtered_df)
        total_pages = (total_records + page_size - 1) // page_size
        
        # Verifica se a página solicitada existe
        if page > total_pages and total_pages > 0:
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Página {page} não existe. Total de páginas disponíveis: {total_pages}",
                    "total_records": total_records,
                    "total_pages": total_pages
                }
            )
        
        # Aplica a paginação (seleciona apenas a página solicitada)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_records)
        
        # Verifica se há dados após a filtragem e paginação
        if total_records == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Nenhuma transação encontrada com os filtros aplicados",
                    "count": 0,
                    "filters_applied": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "transaction_id": transaction_id,
                        "bin_number": bin_number,
                        "min_amount": min_amount,
                        "max_amount": max_amount
                    },
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total_records": 0,
                        "total_pages": 0
                    }
                }
            )
        
        # Seleciona apenas a página atual para processamento
        print(f"Aplicando paginação: página {page} de {total_pages} ({start_idx+1}-{end_idx} de {total_records} registros)")
        paged_df = filtered_df.iloc[start_idx:end_idx].copy()
        
        # 5. Carrega o modelo
        print("Carregando modelo...")
        model = joblib.load(MODEL_PATH)
        
        # 6. Prepara os dados para predição
        print(f"Preparando dados para predição de {len(paged_df)} transações...")
        transaction_ids = paged_df['transaction_id'].tolist() if 'transaction_id' in paged_df.columns else [f"tx_{i}" for i in range(len(paged_df))]
        tx_amounts = paged_df['tx_amount'].tolist() if 'tx_amount' in paged_df.columns else [0.0] * len(paged_df)
        
        # Remove colunas que não são usadas no modelo
        X = paged_df.drop(columns=[col for col in ['transaction_id', 'tx_datetime', 'tx_amount'] if col in paged_df.columns])
        
        # 7. Faz a predição
        print("Fazendo predições...")
        y_pred = model.predict(X)
        y_prob = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else [None]*len(X)
        
        # 8. Monta resultado e salva no banco de dados
        results = []
        
        # Conecta ao banco de dados
        with engine.connect() as conn:
            print("Conectando ao banco de dados...")
            
            # Limpa logs anteriores se solicitado
            if clear_previous_logs:
                print("Limpando logs anteriores...")
                delete_query = delete(prediction_logs)
                conn.execute(delete_query)
                print("Logs anteriores removidos com sucesso.")
            
            # Inserir novos logs
            print(f"Inserindo {len(y_pred)} novos logs...")
            for i in range(len(y_pred)):
                timestamp = datetime.now()
                transaction_id = str(transaction_ids[i])
                is_fraud = bool(y_pred[i])
                tx_amount = float(tx_amounts[i])
                probability = float(y_prob[i]) if y_prob[i] is not None else 0.0
                
                # Salva log no PostgreSQL
                conn.execute(
                    prediction_logs.insert().values(
                        transaction_id=transaction_id,
                        timestamp=timestamp,
                        is_fraud=is_fraud,
                        tx_amount=tx_amount,
                        fraud_probability=probability
                    )
                )
                
                # Adiciona ao resultado da API
                results.append({
                    "transaction_id": transaction_id,
                    "timestamp": timestamp.isoformat(),
                    "is_fraud": is_fraud,
                    "value": tx_amount,
                    "probability": probability
                })
            
            # Commit das transações
            conn.commit()

        return {
            "message": f"Predição realizada com sucesso. {len(results)} logs {'substituídos' if clear_previous_logs else 'adicionados'} no banco.", 
            "results": results, 
            "count": len(results),
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "transaction_id": transaction_id,
                "bin_number": bin_number,
                "min_amount": min_amount,
                "max_amount": max_amount
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "database_log": f"Logs {'substituídos' if clear_previous_logs else 'adicionados'} com sucesso no NeonDB"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro durante a predição: {str(e)}"
        )


        
# @app.post("/upload")
# async def upload_files(
#     payers: UploadFile = File(...),
#     sellers: UploadFile = File(...),
#     transactions: UploadFile = File(...)
# ):
#     try:
#         # Salva arquivos temporariamente
#         payers_path = UPLOAD_DIR / f"payers_{uuid.uuid4()}.feather"
#         sellers_path = UPLOAD_DIR / f"sellers_{uuid.uuid4()}.feather"
#         transactions_path = UPLOAD_DIR / f"transactions_{uuid.uuid4()}.feather"
        
#         for file, path in zip([payers, sellers, transactions], [payers_path, sellers_path, transactions_path]):
#             with open(path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)

#         # Chama o pipeline de merge/features
#         df_features = process_pipeline(payers_path, sellers_path, transactions_path)
#         df_features.to_parquet(FEATURES_PATH, index=False)

#         # Limpa arquivos temporários
#         payers_path.unlink()
#         sellers_path.unlink()
#         transactions_path.unlink()

#         return JSONResponse({"message": "Features geradas com sucesso!", "features_path": str(FEATURES_PATH)})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/predict/batch")
# def predict_batch():
#     try:
#         print(1)
#         # Carrega features
#         if not FEATURES_PATH.exists():
#             raise HTTPException(status_code=400, detail="Arquivo de features não encontrado. Faça upload primeiro.")
#         df = pd.read_parquet(FEATURES_PATH)
#         print(2)
#         # Carrega modelo
#         model = joblib.load(MODEL_PATH)
        
#         # Seleciona as features para o modelo, removendo colunas que não são usadas
#         X = df.drop(columns=[col for col in ['transaction_id', 'tx_datetime', 'tx_amount'] if col in df.columns])
#         print(3)
#         # Faz a predição
#         y_pred = model.predict(X)
#         y_prob = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else [None]*len(X)

#         # Monta resultado e salva no banco de dados
#         results = []
#         print(4)
#         # Conecta ao banco de dados
#         with engine.connect() as conn:
#             for idx, row in df.iterrows():
#                 timestamp = datetime.now()
#                 transaction_id = str(row.get("transaction_id", f"tx_{idx}"))
#                 is_fraud = bool(y_pred[idx])
#                 tx_amount = float(row.get("tx_amount", 0))
#                 probability = float(y_prob[idx]) if y_prob[idx] is not None else 0.0
                
#                 # Salva log no PostgreSQL
#                 conn.execute(
#                     prediction_logs.insert().values(
#                         transaction_id=transaction_id,
#                         timestamp=timestamp,
#                         is_fraud=is_fraud,
#                         tx_amount=tx_amount,
#                         fraud_probability=probability
#                     )
#                 )
#                 print(5)
                
#                 # Adiciona ao resultado da API
#                 results.append({
#                     "transaction_id": transaction_id,
#                     "timestamp": timestamp.isoformat(),
#                     "is_fraud": is_fraud,
#                     "value": tx_amount,
#                     "probability": probability
#                 })
            
#             # Commit das transações
#             conn.commit()

#         return {"results": results, "count": len(results), "database_log": "Logs salvos com sucesso no NeonDB"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erro ao processar predições: {str(e)}")
    






# @app.post("/process-and-predict")
# async def process_and_predict(
#     payers: UploadFile = File(...),
#     sellers: UploadFile = File(...),
#     transactions: UploadFile = File(...),
#     # Filtros
#     start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
#     end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
#     transaction_id: Optional[str] = Query(None, description="ID específico da transação"),
#     bin_number: Optional[str] = Query(None, description="BIN (primeiros 6 dígitos do cartão)"),
#     min_amount: Optional[float] = Query(None, description="Valor mínimo da transação"),
#     max_amount: Optional[float] = Query(None, description="Valor máximo da transação"),
#     # Paginação
#     page: int = Query(1, ge=1, description="Página a processar (1000 transações por página)"),
#     page_size: int = Query(1000, ge=10, le=10000, description="Número de transações por página")
# ):
#     try:
#         # 1. Salva arquivos temporariamente
#         payers_path = UPLOAD_DIR / f"payers_{uuid.uuid4()}.feather"
#         sellers_path = UPLOAD_DIR / f"sellers_{uuid.uuid4()}.feather"
#         transactions_path = UPLOAD_DIR / f"transactions_{uuid.uuid4()}.feather"
        
#         UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
#         for file, path in zip([payers, sellers, transactions], [payers_path, sellers_path, transactions_path]):
#             with open(path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)

#         # 2. Processa os dados e gera features
#         print("Processando dados...")
#         df_features = process_pipeline(payers_path, sellers_path, transactions_path)
        
#         # 3. Aplica filtros antes de paginar
#         print("Aplicando filtros...")
#         filtered_df = df_features.copy()
        
#         # Filtros de data
#         if start_date and 'tx_datetime' in filtered_df.columns:
#             filtered_df = filtered_df[filtered_df['tx_datetime'] >= pd.to_datetime(start_date)]
            
#         if end_date and 'tx_datetime' in filtered_df.columns:
#             filtered_df = filtered_df[filtered_df['tx_datetime'] <= pd.to_datetime(end_date)]
        
#         # Filtro por ID da transação
#         if transaction_id and 'transaction_id' in filtered_df.columns:
#             filtered_df = filtered_df[filtered_df['transaction_id'].str.contains(transaction_id, na=False)]
        
#         # Filtro por BIN
#         if bin_number and 'transaction_id' in filtered_df.columns:
#             filtered_df = filtered_df[filtered_df['transaction_id'].str.startswith(bin_number, na=False)]
        
#         # Filtros de valor
#         if min_amount is not None and 'tx_amount' in filtered_df.columns:
#             filtered_df = filtered_df[filtered_df['tx_amount'] >= min_amount]
            
#         if max_amount is not None and 'tx_amount' in filtered_df.columns:
#             filtered_df = filtered_df[filtered_df['tx_amount'] <= max_amount]
        
#         # 4. Aplicar paginação no conjunto filtrado
#         total_records = len(filtered_df)
#         total_pages = (total_records + page_size - 1) // page_size
        
#         # Verifica se a página solicitada existe
#         if page > total_pages and total_pages > 0:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "message": f"Página {page} não existe. Total de páginas disponíveis: {total_pages}",
#                     "total_records": total_records,
#                     "total_pages": total_pages
#                 }
#             )
        
#         # Aplica a paginação (seleciona apenas a página solicitada)
#         start_idx = (page - 1) * page_size
#         end_idx = min(start_idx + page_size, total_records)
        
#         # Verifica se há dados após a filtragem e paginação
#         if total_records == 0:
#             return JSONResponse(
#                 status_code=200,
#                 content={
#                     "message": "Nenhuma transação encontrada com os filtros aplicados",
#                     "count": 0,
#                     "filters_applied": {
#                         "start_date": start_date,
#                         "end_date": end_date,
#                         "transaction_id": transaction_id,
#                         "bin_number": bin_number,
#                         "min_amount": min_amount,
#                         "max_amount": max_amount
#                     },
#                     "pagination": {
#                         "page": page,
#                         "page_size": page_size,
#                         "total_records": 0,
#                         "total_pages": 0
#                     }
#                 }
#             )
        
#         # Seleciona apenas a página atual para processamento
#         print(f"Aplicando paginação: página {page} de {total_pages}")
#         paged_df = filtered_df.iloc[start_idx:end_idx].copy()
        
#         # 5. Carrega o modelo
#         print("Carregando modelo...")
#         model = joblib.load(MODEL_PATH)
        
#         # 6. Prepara os dados para predição
#         print(f"Preparando dados para predição de {len(paged_df)} transações...")
#         transaction_ids = paged_df['transaction_id'].tolist() if 'transaction_id' in paged_df.columns else [f"tx_{i}" for i in range(len(paged_df))]
#         tx_amounts = paged_df['tx_amount'].tolist() if 'tx_amount' in paged_df.columns else [0.0] * len(paged_df)
        
#         print("Removendo colunas desnecessárias...")
#         # Remove colunas que não são usadas no modelo
#         X = paged_df.drop(columns=[col for col in ['transaction_id', 'tx_datetime', 'tx_amount'] if col in paged_df.columns])
        
#         # 7. Faz a predição
#         print("Fazendo predições...")
#         y_pred = model.predict(X)
#         y_prob = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else [None]*len(X)
        
#         # 8. Monta resultado e salva no banco de dados
#         results = []
        
#         # Conecta ao banco de dados
#         with engine.connect() as conn:
#             print("Conectando ao banco de dados...")
#             for i in range(len(y_pred)):
#                 timestamp = datetime.now()
#                 transaction_id = str(transaction_ids[i])
#                 is_fraud = bool(y_pred[i])
#                 tx_amount = float(tx_amounts[i])
#                 probability = float(y_prob[i]) if y_prob[i] is not None else 0.0
                
#                 # Salva log no PostgreSQL
#                 conn.execute(
#                     prediction_logs.insert().values(
#                         transaction_id=transaction_id,
#                         timestamp=timestamp,
#                         is_fraud=is_fraud,
#                         tx_amount=tx_amount,
#                         fraud_probability=probability
#                     )
#                 )
                
#                 # Adiciona ao resultado da API
#                 results.append({
#                     "transaction_id": transaction_id,
#                     "timestamp": timestamp.isoformat(),
#                     "is_fraud": is_fraud,
#                     "value": tx_amount,
#                     "probability": probability
#                 })
            
#             # Commit das transações
#             conn.commit()
        
#         # 9. Limpa arquivos temporários
#         payers_path.unlink(missing_ok=True)
#         sellers_path.unlink(missing_ok=True)
#         transactions_path.unlink(missing_ok=True)

#         return {
#             "message": "Processamento e predição completos", 
#             "results": results, 
#             "count": len(results),
#             "filters_applied": {
#                 "start_date": start_date,
#                 "end_date": end_date,
#                 "transaction_id": transaction_id,
#                 "bin_number": bin_number,
#                 "min_amount": min_amount,
#                 "max_amount": max_amount
#             },
#             "pagination": {
#                 "page": page,
#                 "page_size": page_size,
#                 "total_records": total_records,
#                 "total_pages": total_pages,
#                 "has_next": page < total_pages,
#                 "has_previous": page > 1
#             },
#             "database_log": "Logs salvos com sucesso no NeonDB"
#         }
#     except Exception as e:
#         # Tenta limpar arquivos em caso de erro
#         try:
#             payers_path.unlink(missing_ok=True)
#             sellers_path.unlink(missing_ok=True)
#             transactions_path.unlink(missing_ok=True)

#         except:
#             pass
        
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Erro durante o processamento: {str(e)}"
#         )
    


    ## FAZENDO O PROCESSAMENTO E PREDIÇÃO SEPARADOS




