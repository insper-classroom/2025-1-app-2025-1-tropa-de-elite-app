"""
Utilitário para manipular logs de transações e predições.
"""
import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

class LogHandler:
    """Classe para manipular logs de transações e predições."""
    
    def __init__(self, db_path: str = "logs/fraud_logs.db"):
        """
        Inicializa o manipulador de logs.
        
        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Inicializa o banco de dados SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Cria tabela de logs se não existir
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    transaction_id TEXT,
                    user_id TEXT,
                    score REAL,
                    decision TEXT,
                    model_version TEXT,
                    attributes TEXT
                )
                ''')
                
                conn.commit()
        except Exception as e:
            logger.exception(f"Erro ao inicializar banco de dados: {str(e)}")
    
    def log_prediction(self, prediction: Dict[str, Any], user_id: str = "system") -> str:
        """
        Registra uma predição no banco de dados.
        
        Args:
            prediction: Resultado da predição
            user_id: ID do usuário que solicitou a predição
            
        Returns:
            ID do log gerado
        """
        try:
            log_id = str(uuid.uuid4())
            transaction_id = prediction.get("attributes", {}).get("id", "unknown")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO logs (id, timestamp, transaction_id, user_id, score, decision, model_version, attributes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log_id,
                    prediction.get("timestamp", datetime.now().isoformat()),
                    transaction_id,
                    user_id,
                    prediction.get("score", 0.0),
                    prediction.get("decision", "UNKNOWN"),
                    prediction.get("version", "unknown"),
                    json.dumps(prediction.get("attributes", {}))
                ))
                
                conn.commit()
            
            logger.info(f"Log salvo para transação {transaction_id}")
            return log_id
        
        except Exception as e:
            logger.exception(f"Erro ao salvar log: {str(e)}")
            return str(uuid.uuid4())  # Retorna um ID mesmo em caso de erro
    
    def get_logs(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_version: Optional[str] = None,
        fraud_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtém logs com base em filtros.
        
        Args:
            start_date: Data de início
            end_date: Data de fim
            model_version: Versão do modelo
            fraud_only: Apenas logs de fraude
            limit: Limite de resultados
            
        Returns:
            Lista de logs
        """
        try:
            query = "SELECT * FROM logs"
            params = []
            where_clauses = []
            
            # Aplica filtros
            if start_date:
                where_clauses.append("timestamp >= ?")
                params.append(start_date.isoformat())
            
            if end_date:
                where_clauses.append("timestamp <= ?")
                params.append(end_date.isoformat())
            
            if model_version:
                where_clauses.append("model_version = ?")
                params.append(model_version)
            
            if fraud_only:
                where_clauses.append("decision = 'FRAUD'")
            
            # Adiciona cláusulas WHERE se houver
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Ordena por timestamp decrescente e limita resultados
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                logs = []
                for row in cursor.fetchall():
                    log = dict(row)
                    
                    # Converte atributos de JSON para dicionário
                    if 'attributes' in log and log['attributes']:
                        log['attributes'] = json.loads(log['attributes'])
                    
                    # Ajusta formato para corresponder ao schema da API
                    logs.append({
                        "id": log["id"],
                        "timestamp": log["timestamp"],
                        "transactionId": log["transaction_id"],
                        "userId": log["user_id"],
                        "score": log["score"],
                        "decision": log["decision"],
                        "version": log["model_version"],
                        "attributes": log.get("attributes", {})
                    })
                
                return logs
        
        except Exception as e:
            logger.exception(f"Erro ao obter logs: {str(e)}")
            return []
