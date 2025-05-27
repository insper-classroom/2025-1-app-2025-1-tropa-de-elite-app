"""
Script para inicializar dados de exemplo para o backend.
"""
import os
import sys
import json
import pandas as pd
import pyarrow.feather as feather
from datetime import datetime, timedelta
import random
import uuid

# Adiciona o diretório pai ao path para importar os módulos do backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_handler import DataHandler
from utils.log_handler import LogHandler

def create_sample_transactions(n=50):
    """Cria transações de exemplo."""
    transactions = {}
    
    for i in range(n):
        tx_id = f"TX-{1000 + i}"
        timestamp = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        
        transaction = {
            "id": tx_id,
            "timestamp": timestamp,
            "amount": round(random.uniform(10, 5000), 2),
            "merchantId": f"MERCH-{random.randint(1, 20)}",
            "customerId": f"CUST-{random.randint(1, 100)}",
            "cardType": random.choice(["VISA", "MASTERCARD", "AMEX", "ELO"]),
            "ipAddress": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "deviceId": random.choice(["iPhone", "Galaxy", "Pixel"]) + f"-{random.randint(10, 20)}",
            "location": random.choice(["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Porto Alegre", "Recife"]),
            "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
            "os": random.choice(["iOS", "Android", "Windows", "macOS"]),
            "transactionType": random.choice(["online", "mobile", "in-store"])
        }
        
        transactions[tx_id] = transaction
    
    return transactions

def create_sample_logs(transactions, n=100):
    """Cria logs de exemplo."""
    logs = []
    
    for i in range(n):
        # Usa transações existentes ou gera IDs aleatórios
        if i < len(transactions):
            tx_id = list(transactions.keys())[i]
            tx = transactions[tx_id]
        else:
            tx_id = f"TX-{2000 + i}"
            tx = {
                "id": tx_id,
                "amount": round(random.uniform(10, 5000), 2),
                "merchantId": f"MERCH-{random.randint(1, 20)}",
                "customerId": f"CUST-{random.randint(1, 100)}"
            }
        
        # Gera um score aleatório para fraude
        score = random.random()
        decision = "FRAUD" if score > 0.7 else "NOT_FRAUD"
        
        log = {
            "id": str(uuid.uuid4()),
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 60 * 24 * 7))).isoformat(),
            "transactionId": tx_id,
            "userId": "system",
            "score": score,
            "decision": decision,
            "version": "v1.0.0",
            "attributes": tx
        }
        
        logs.append(log)
    
    return logs

def init_sample_data():
    """Inicializa dados de exemplo."""
    # Cria diretórios necessários
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Cria transações de exemplo
    transactions = create_sample_transactions(50)
    
    # Salva transações em um arquivo JSON
    with open(os.path.join("data", "transactions.json"), "w") as f:
        json.dump(transactions, f, indent=2)
    
    print(f"Criadas {len(transactions)} transações de exemplo.")
    
    # Inicializa o handler de logs
    log_handler = LogHandler(db_path=os.path.join("logs", "fraud_logs.db"))
    
    # Cria logs de exemplo
    logs = create_sample_logs(transactions, 100)
    
    # Salva logs no banco de dados
    for log in logs:
        log_handler.log_prediction({
            "decision": log["decision"],
            "score": log["score"],
            "version": log["version"],
            "timestamp": log["timestamp"],
            "attributes": log["attributes"]
        }, log["userId"])
    
    print(f"Criados {len(logs)} logs de exemplo.")

if __name__ == "__main__":
    print("Inicializando dados de exemplo...")
    init_sample_data()
    print("Dados de exemplo inicializados com sucesso!")
