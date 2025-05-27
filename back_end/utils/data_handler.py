"""
Utilitário para manipular dados de transações.
"""
import os
import json
import pandas as pd
import pyarrow.feather as feather
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

class DataHandler:
    """Classe para manipular dados de transações."""
    
    def __init__(self, data_dir: str, dvc_repo_path: str):
        """
        Inicializa o manipulador de dados.
        
        Args:
            data_dir: Diretório para salvar os dados
            dvc_repo_path: Caminho para o repositório DVC
        """
        self.data_dir = data_dir
        self.dvc_repo_path = dvc_repo_path
        self.transactions_path = os.path.join(data_dir, "transactions.json")
        self.dataset_path = os.path.join(dvc_repo_path, "data", "data_features_v1.feather")
        
        # Inicializa o diretório de dados
        os.makedirs(data_dir, exist_ok=True)
        
        # Carrega transações existentes ou cria um novo arquivo
        self._load_transactions()
    
    def _load_transactions(self) -> None:
        """Carrega transações do arquivo JSON."""
        try:
            if os.path.exists(self.transactions_path):
                with open(self.transactions_path, 'r') as f:
                    self.transactions = json.load(f)
            else:
                self.transactions = {}
                self._save_transactions()
        except Exception as e:
            logger.exception(f"Erro ao carregar transações: {str(e)}")
            self.transactions = {}
    
    def _save_transactions(self) -> None:
        """Salva transações no arquivo JSON."""
        try:
            with open(self.transactions_path, 'w') as f:
                json.dump(self.transactions, f, indent=2)
        except Exception as e:
            logger.exception(f"Erro ao salvar transações: {str(e)}")
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém uma transação pelo ID.
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            Dicionário com os dados da transação ou None se não encontrada
        """
        # Verifica se a transação existe no cache local
        if transaction_id in self.transactions:
            return self.transactions[transaction_id]
        
        # Se não encontrou, verifica no dataset DVC
        try:
            if os.path.exists(self.dataset_path):
                # Carrega o dataset para buscar a transação
                df = feather.read_feather(self.dataset_path)
                
                # Busca a transação pelo ID
                if 'transaction_id' in df.columns:
                    tx = df[df['transaction_id'] == transaction_id]
                    if not tx.empty:
                        # Converte para o formato da API
                        transaction = self._convert_transaction(tx.iloc[0])
                        # Adiciona ao cache
                        self.transactions[transaction_id] = transaction
                        self._save_transactions()
                        return transaction
        except Exception as e:
            logger.exception(f"Erro ao buscar transação no dataset: {str(e)}")
        
        # Se não encontrou ou ocorreu um erro, retorna None
        return None
    
    def _convert_transaction(self, row: pd.Series) -> Dict[str, Any]:
        """
        Converte uma linha do DataFrame para o formato de transação da API.
        
        Args:
            row: Linha do DataFrame
            
        Returns:
            Dicionário no formato de transação da API
        """
        # Mapeia colunas do dataset para o formato da API
        # Ajuste conforme necessário para seu dataset
        transaction = {
            "id": str(row.get('transaction_id', '')),
            "timestamp": row.get('tx_datetime', datetime.now()).isoformat(),
            "amount": float(row.get('tx_amount', 0.0)),
            "merchantId": str(row.get('terminal_id', '')),
            "customerId": str(row.get('card_id', '')),
            "cardType": str(row.get('card_bin', '')),
            "location": f"{row.get('latitude', 0.0)},{row.get('longitude', 0.0)}",
        }
        
        # Adiciona campos adicionais se existirem
        for col in row.index:
            if col not in ['transaction_id', 'tx_datetime', 'tx_amount', 'terminal_id', 'card_id', 'card_bin', 'latitude', 'longitude']:
                # Ignora campos com valores nulos
                if pd.notna(row[col]):
                    # Converte tipos numpy para tipos Python nativos
                    if hasattr(row[col], 'item'):
                        transaction[col] = row[col].item()
                    else:
                        transaction[col] = row[col]
        
        return transaction
    
    def add_transaction(self, transaction: Dict[str, Any]) -> str:
        """
        Adiciona uma nova transação.
        
        Args:
            transaction: Dicionário com os dados da transação
            
        Returns:
            ID da transação adicionada
        """
        # Gera um ID se não existir
        if 'id' not in transaction:
            transaction['id'] = f"TX-{len(self.transactions) + 1}"
        
        # Adiciona timestamp se não existir
        if 'timestamp' not in transaction:
            transaction['timestamp'] = datetime.now().isoformat()
        
        # Adiciona ao cache
        self.transactions[transaction['id']] = transaction
        self._save_transactions()
        
        return transaction['id']
    
    def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém uma lista de transações.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de transações
        """
        # Retorna as últimas 'limit' transações
        return list(self.transactions.values())[-limit:]
    
    def load_dataset_sample(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Carrega uma amostra do dataset DVC.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de transações
        """
        try:
            if os.path.exists(self.dataset_path):
                # Carrega o dataset
                df = feather.read_feather(self.dataset_path)
                
                # Limita o número de linhas
                sample = df.head(limit)
                
                # Converte para o formato da API
                transactions = []
                for _, row in sample.iterrows():
                    transaction = self._convert_transaction(row)
                    transactions.append(transaction)
                    
                    # Adiciona ao cache
                    self.transactions[transaction['id']] = transaction
                
                self._save_transactions()
                return transactions
            else:
                logger.warning(f"Dataset não encontrado: {self.dataset_path}")
                return []
        except Exception as e:
            logger.exception(f"Erro ao carregar dataset: {str(e)}")
            return []
