"""
Utilitário para gerenciar jobs de processamento em lote.
"""
import os
import json
import uuid
import time
import threading
import pandas as pd
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

class BatchJobHandler:
    """Classe para gerenciar jobs de processamento em lote."""
    
    def __init__(self, jobs_dir: str):
        """
        Inicializa o gerenciador de jobs.
        
        Args:
            jobs_dir: Diretório para salvar os jobs
        """
        self.jobs_dir = jobs_dir
        self.jobs_file = os.path.join(jobs_dir, "batch_jobs.json")
        self.results_dir = os.path.join(jobs_dir, "results")
        
        # Inicializa os diretórios
        os.makedirs(self.jobs_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Carrega jobs existentes ou cria um novo arquivo
        self._load_jobs()
    
    def _load_jobs(self) -> None:
        """Carrega jobs do arquivo JSON."""
        try:
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, 'r') as f:
                    self.jobs = json.load(f)
            else:
                self.jobs = {}
                self._save_jobs()
        except Exception as e:
            logger.exception(f"Erro ao carregar jobs: {str(e)}")
            self.jobs = {}
    
    def _save_jobs(self) -> None:
        """Salva jobs no arquivo JSON."""
        try:
            with open(self.jobs_file, 'w') as f:
                json.dump(self.jobs, f, indent=2)
        except Exception as e:
            logger.exception(f"Erro ao salvar jobs: {str(e)}")
    
    def create_job(self, file_path: str, user_id: str = "system") -> str:
        """
        Cria um novo job de processamento em lote.
        
        Args:
            file_path: Caminho do arquivo a ser processado
            user_id: ID do usuário que criou o job
            
        Returns:
            ID do job criado
        """
        job_id = str(uuid.uuid4())
        
        # Cria o job
        self.jobs[job_id] = {
            "jobId": job_id,
            "progress": 0,
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "userId": user_id,
            "filePath": file_path,
            "downloadUrl": None
        }
        
        # Salva os jobs
        self._save_jobs()
        
        # Inicia o processamento em uma thread separada
        threading.Thread(target=self._process_job, args=(job_id,)).start()
        
        return job_id
    
    def _process_job(self, job_id: str) -> None:
        """
        Processa um job em segundo plano.
        
        Args:
            job_id: ID do job a ser processado
        """
        try:
            if job_id not in self.jobs:
                logger.error(f"Job não encontrado: {job_id}")
                return
            
            # Atualiza o status para processando
            self.jobs[job_id]["status"] = "processing"
            self._save_jobs()
            
            # Obtém o caminho do arquivo
            file_path = self.jobs[job_id]["filePath"]
            
            # Verifica se o arquivo existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Em um sistema real, você processaria o arquivo de acordo com seu formato
            # Por simplicidade, vamos simular o processamento
            total_steps = 10
            for step in range(total_steps):
                # Atualiza o progresso
                self.jobs[job_id]["progress"] = (step + 1) * 100 // total_steps
                self._save_jobs()
                
                # Simula processamento
                time.sleep(1)
            
            # Gera o arquivo de resultados
            result_path = os.path.join(self.results_dir, f"{job_id}.csv")
            
            # Em um sistema real, você processaria os dados e geraria o resultado
            # Por simplicidade, vamos criar um CSV de exemplo
            self._generate_dummy_results(result_path)
            
            # Atualiza o job com sucesso
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["progress"] = 100
            self.jobs[job_id]["downloadUrl"] = f"/api/predict/batch/{job_id}/download"
            self._save_jobs()
            
            logger.info(f"Job {job_id} concluído com sucesso")
            
        except Exception as e:
            logger.exception(f"Erro ao processar job {job_id}: {str(e)}")
            
            # Atualiza o job com erro
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = str(e)
                self._save_jobs()
    
    def _generate_dummy_results(self, result_path: str) -> None:
        """
        Gera um arquivo CSV de resultados de exemplo.
        
        Args:
            result_path: Caminho para salvar o arquivo
        """
        try:
            # Cria um DataFrame de exemplo
            data = []
            for i in range(100):
                score = round(0.1 + 0.8 * (i % 10) / 10, 2)
                decision = "FRAUD" if score > 0.7 else "NOT_FRAUD"
                
                data.append({
                    "transaction_id": f"TX-{i+1000}",
                    "timestamp": datetime.now().isoformat(),
                    "amount": round(100 + i * 10, 2),
                    "score": score,
                    "decision": decision,
                    "version": "v1.0.0"
                })
            
            # Cria o DataFrame e salva como CSV
            df = pd.DataFrame(data)
            df.to_csv(result_path, index=False)
            
        except Exception as e:
            logger.exception(f"Erro ao gerar resultados dummy: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o status de um job.
        
        Args:
            job_id: ID do job
            
        Returns:
            Dicionário com o status do job ou None se não encontrado
        """
        return self.jobs.get(job_id)
    
    def get_result_path(self, job_id: str) -> Optional[str]:
        """
        Obtém o caminho do arquivo de resultados de um job.
        
        Args:
            job_id: ID do job
            
        Returns:
            Caminho do arquivo de resultados ou None se não encontrado
        """
        if job_id in self.jobs and self.jobs[job_id]["status"] == "completed":
            return os.path.join(self.results_dir, f"{job_id}.csv")
        return None
