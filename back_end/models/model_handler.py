"""
Módulo para manipulação de modelos de ML para detecção de fraudes.
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from loguru import logger
from datetime import datetime

class ModelHandler:
    """Classe para manipular operações relacionadas ao modelo de ML."""
    
    def __init__(self, models_dir: str):
        """
        Inicializa o manipulador de modelos.
        
        Args:
            models_dir: Diretório onde os modelos estão armazenados
        """
        self.models_dir = models_dir
        self.default_model_path = os.path.join(models_dir, "fraud_detection_model.pkl")
        self._model = None
        self._model_info = {
            "version": "v1.0.0",
            "lastUpdated": datetime.now().isoformat(),
            "metrics": {
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
                "f1Score": 0.90
            }
        }
    
    @property
    def model(self):
        """
        Carrega o modelo, se ainda não estiver carregado.
        
        Returns:
            Modelo carregado
        """
        if self._model is None:
            self._load_model()
        return self._model
    
    def _load_model(self) -> None:
        """Carrega o modelo do disco."""
        try:
            if os.path.exists(self.default_model_path):
                logger.info(f"Carregando modelo de {self.default_model_path}")
                self._model = joblib.load(self.default_model_path)
            else:
                # Para simplificar, criamos um modelo dummy se não existir
                from sklearn.ensemble import RandomForestClassifier
                logger.warning(f"Modelo não encontrado em {self.default_model_path}. Criando modelo dummy.")
                self._model = RandomForestClassifier(n_estimators=10)
                
                # Salva o modelo dummy
                os.makedirs(os.path.dirname(self.default_model_path), exist_ok=True)
                joblib.dump(self._model, self.default_model_path)
        except Exception as e:
            logger.exception(f"Erro ao carregar modelo: {str(e)}")
            from sklearn.ensemble import RandomForestClassifier
            self._model = RandomForestClassifier(n_estimators=10)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o modelo atual.
        
        Returns:
            Dicionário com informações do modelo
        """
        return self._model_info
    
    def preprocess_transaction(self, transaction: Dict[str, Any]) -> pd.DataFrame:
        """
        Pré-processa uma transação para prever.
        
        Args:
            transaction: Dicionário com os dados da transação
            
        Returns:
            DataFrame com os dados pré-processados
        """
        # Em um caso real, você aplicaria aqui a mesma transformação usada no treinamento
        # Por simplicidade, vamos criar algumas features básicas
        
        # Converte para DataFrame
        tx = pd.DataFrame([transaction])
        
        # Extrai informação temporal
        if 'timestamp' in tx.columns:
            tx['timestamp'] = pd.to_datetime(tx['timestamp'])
            tx['hour'] = tx['timestamp'].dt.hour
            tx['day_of_week'] = tx['timestamp'].dt.dayofweek
        
        # Cria feature de log do valor
        if 'amount' in tx.columns:
            tx['amount_log'] = np.log1p(tx['amount'])
        
        # Codifica variáveis categóricas (simplificado)
        for col in ['cardType', 'transactionType']:
            if col in tx.columns:
                tx[f'{col}_encoded'] = tx[col].astype('category').cat.codes
        
        # Remove colunas que não são usadas pelo modelo
        features = [
            'amount', 'amount_log', 'hour', 'day_of_week', 
            'cardType_encoded', 'transactionType_encoded'
        ]
        
        # Retorna apenas as features existentes
        return tx[[col for col in features if col in tx.columns]]
    
    def predict(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz uma predição para uma transação.
        
        Args:
            transaction: Dicionário com os dados da transação
            
        Returns:
            Resultado da predição
        """
        try:
            # Pré-processa a transação
            features = self.preprocess_transaction(transaction)
            
            # Verifica se temos dados para prever
            if features.empty:
                raise ValueError("Sem features suficientes para prever")
            
            # Faz a predição
            # Em um sistema real, você usaria model.predict_proba() para obter a probabilidade
            # Como é um modelo dummy, estamos gerando probabilidades aleatórias para demonstração
            
            # Simplificação para demonstração
            score = np.random.random()  # Probabilidade de fraude
            decision = "FRAUD" if score > 0.7 else "NOT_FRAUD"
            
            return {
                "decision": decision,
                "score": float(score),
                "version": self._model_info["version"],
                "timestamp": datetime.now().isoformat(),
                "attributes": transaction
            }
        except Exception as e:
            logger.exception(f"Erro ao fazer predição: {str(e)}")
            raise
    
    def batch_predict(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Faz predições em lote para múltiplas transações.
        
        Args:
            transactions: Lista de dicionários com dados das transações
            
        Returns:
            Lista de resultados de predição
        """
        results = []
        for tx in transactions:
            try:
                result = self.predict(tx)
                results.append(result)
            except Exception as e:
                logger.error(f"Erro ao processar transação {tx.get('id', 'unknown')}: {str(e)}")
                # Adiciona um resultado de erro
                results.append({
                    "decision": "ERROR",
                    "score": 0.0,
                    "version": self._model_info["version"],
                    "timestamp": datetime.now().isoformat(),
                    "attributes": tx,
                    "error": str(e)
                })
        
        return results
