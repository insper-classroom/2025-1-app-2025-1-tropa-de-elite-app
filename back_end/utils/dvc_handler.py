"""
Utilitários para trabalhar com DVC no backend.
"""
import os
import subprocess
import json
from loguru import logger
from typing import Dict, Any, Optional, List, Tuple

class DVCHandler:
    """Classe para lidar com operações do DVC."""
    
    def __init__(self, dvc_repo_path: str):
        """
        Inicializa o manipulador DVC.
        
        Args:
            dvc_repo_path: Caminho para o repositório DVC
        """
        self.dvc_repo_path = dvc_repo_path
        self.models_path = os.path.join(dvc_repo_path, "models")
        self.data_path = os.path.join(dvc_repo_path, "data")
        
        # Verifica se os diretórios existem, criando-os se necessário
        os.makedirs(self.models_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)
    
    def run_dvc_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Executa um comando DVC.
        
        Args:
            command: Lista com o comando DVC a ser executado
            
        Returns:
            Tupla (sucesso, output)
        """
        try:
            result = subprocess.run(
                ["dvc"] + command,
                cwd=self.dvc_repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                logger.error(f"Erro ao executar comando DVC: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            logger.exception(f"Erro ao executar comando DVC: {str(e)}")
            return False, str(e)
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o modelo atual.
        
        Returns:
            Dicionário com informações do modelo
        """
        # Verifica a versão do DVC
        success, dvc_version_output = self.run_dvc_command(["version"])
        dvc_version = dvc_version_output.strip() if success else "Unknown"
        
        # Obtém metadados do último modelo (pode ser customizado conforme seu projeto)
        model_path = os.path.join(self.models_path, "fraud_detection_model.pkl")
        model_exists = os.path.exists(model_path)
        
        # Obtém métricas do modelo, se disponíveis
        metrics = {}
        metrics_path = os.path.join(self.dvc_repo_path, "metrics.json")
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r') as f:
                    metrics = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar métricas: {str(e)}")
        
        # Monta informações do modelo
        model_info = {
            "version": "v1.0.0",  # Versão padrão, deve ser atualizada com seu esquema de versão
            "dvcVersion": dvc_version,
            "modelPath": model_path if model_exists else None,
            "lastUpdated": None,  # Deve ser atualizado com a data real de atualização
            "metrics": metrics
        }
        
        return model_info
    
    def add_to_dvc(self, file_path: str) -> bool:
        """
        Adiciona um arquivo ao DVC.
        
        Args:
            file_path: Caminho do arquivo a ser adicionado
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return False
        
        relative_path = os.path.relpath(file_path, self.dvc_repo_path)
        success, output = self.run_dvc_command(["add", relative_path])
        
        if success:
            logger.info(f"Arquivo {file_path} adicionado ao DVC com sucesso")
            return True
        else:
            logger.error(f"Erro ao adicionar arquivo ao DVC: {output}")
            return False
    
    def pull_data(self, path: Optional[str] = None) -> bool:
        """
        Puxa dados do repositório remoto DVC.
        
        Args:
            path: Caminho específico para puxar (opcional)
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        command = ["pull"]
        if path:
            command.append(path)
        
        success, output = self.run_dvc_command(command)
        
        if success:
            logger.info("Dados DVC puxados com sucesso")
            return True
        else:
            logger.error(f"Erro ao puxar dados DVC: {output}")
            return False
    
    def push_data(self, path: Optional[str] = None) -> bool:
        """
        Envia dados para o repositório remoto DVC.
        
        Args:
            path: Caminho específico para enviar (opcional)
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        command = ["push"]
        if path:
            command.append(path)
        
        success, output = self.run_dvc_command(command)
        
        if success:
            logger.info("Dados DVC enviados com sucesso")
            return True
        else:
            logger.error(f"Erro ao enviar dados DVC: {output}")
            return False
