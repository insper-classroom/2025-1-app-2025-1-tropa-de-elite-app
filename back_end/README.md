# Backend para Sistema de Detecção de Fraudes

Este é o backend do sistema de detecção de fraudes desenvolvido pelo time Tropa de Elite. O backend fornece uma API RESTful para interação com modelos de detecção de fraudes, gerenciamento de dados e logs de transações.

## Tecnologias Utilizadas

- **FastAPI**: Framework web para construção de APIs com Python
- **SQLite**: Banco de dados para armazenamento de logs
- **DVC**: Versionamento de dados e modelos
- **Pandas/PyArrow**: Processamento de dados
- **Scikit-learn**: Biblioteca para machine learning
- **Loguru**: Sistema de logging avançado

## Estrutura do Projeto

```
back_end/
├── api/                   # Definições da API
│   ├── routes/            # Rotas da API
│   └── schemas.py         # Esquemas de dados da API
├── data/                  # Dados locais e cache
├── logs/                  # Logs da aplicação
├── models/                # Modelos de ML
│   └── model_handler.py   # Manipulador de modelos
├── utils/                 # Utilitários
│   ├── batch_handler.py   # Manipulador de jobs em lote
│   ├── data_handler.py    # Manipulador de dados
│   ├── dvc_handler.py     # Integração com DVC
│   └── log_handler.py     # Manipulador de logs
├── .env                   # Variáveis de ambiente
├── main.py                # Ponto de entrada da aplicação
└── requirements.txt       # Dependências do projeto
```

## Instalação

1. Certifique-se de ter Python 3.9+ instalado.
2. Clone o repositório.
3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente no arquivo `.env`.
5. Inicialize os dados de exemplo:

```bash
python utils/init_data.py
```

## Execução

Para iniciar o servidor:

```bash
uvicorn main:app --reload
```

O servidor estará disponível em `http://localhost:8000`.

## Documentação da API

A documentação interativa da API estará disponível em `http://localhost:8000/docs`.

## Endpoints Principais

- `/api/models/current`: Obter informações sobre o modelo atual
- `/api/transactions/{id}`: Obter detalhes de uma transação
- `/api/predict/transaction/{id}`: Fazer uma predição de fraude para uma transação
- `/api/predict/batch`: Enviar um job de processamento em lote
- `/api/logs`: Obter logs de predições

## Integração com DVC

O backend se integra com o DVC (Data Version Control) para rastrear versões de dados e modelos. A configuração do repositório DVC é feita através da variável de ambiente `DVC_REPO_PATH`.

## Desenvolvimento

Para contribuir com o projeto:

1. Certifique-se de seguir as convenções de código PEP 8.
2. Escreva testes para novas funcionalidades.
3. Execute os testes antes de enviar uma contribuição:

```bash
pytest
```

## Requisitos

Este backend foi desenvolvido para atender aos requisitos da Sprint 2025-1 do Insper, incluindo:

- Versionamento de dados e modelos
- API para uso do modelo (transação única e em lote)
- Sistema de logging para monitoramento
- Integração com o frontend
