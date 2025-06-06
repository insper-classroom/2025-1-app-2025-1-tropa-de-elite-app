[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/NwGJvKsU)

# Sistema de Detecção de Fraudes - Tropa de Elite

Tema: **Prevenção de Fraudes**

Empresa parceira: **Mercado Livre**

## Equipe

MLOps: Pedro Fardin e Mateus Porto

MLEng: Vitor Raia e João Faus

## Estrutura do Projeto

```
.
├── back_end/              # API e serviços de backend
│   ├── api/               # Definições da API
│   ├── models/            # Modelos de ML
│   ├── utils/             # Utilitários
│   └── main.py            # Ponto de entrada do backend
├── front_end/             # Interface de usuário
│   ├── app/               # Páginas do Next.js
│   ├── components/        # Componentes React
│   ├── lib/               # Utilitários do frontend
│   └── types/             # Definições de tipos TypeScript
├── start.bat              # Script para iniciar o sistema (Windows)
└── start.sh               # Script para iniciar o sistema (Linux/macOS)
```

## Pré-requisitos

- Python 3.9+
- Node.js 18+
- npm ou yarn

## Instalação

### Backend

```bash
cd back_end
pip install -r requirements.txt
python utils/init_data.py
```

### Frontend

```bash
cd project
npm install
```

## Execução

Para iniciar todo o sistema de uma vez:

- Windows: Execute `start.bat`
- Linux/macOS: Execute `./start.sh`

Para iniciar os componentes separadamente:

### Backend

```bash
cd back_end
uvicorn main:app --reload
```

### Frontend

```bash
cd project
npm run dev
```

## Funcionalidades

- Dashboard de análise de fraudes em tempo real
- Análise individual de transações
- Processamento em lote de múltiplas transações
- Histórico e logs de detecções
- Integração com DVC para versionamento de modelos e dados

## Documentação

- Documentação da API: http://localhost:8000/docs
- Arquivos README detalhados estão disponíveis em cada diretório

## Integração com o Projeto de Análise de Dados

Este sistema integra-se com o projeto de análise de dados da equipe, localizado em:
`C:\Users\mateu\OneDrive\Documentos\Quarto_sem\Sprint\2025-1-tropa-de-elite`

A integração é feita através do DVC, que permite o versionamento e compartilhamento dos modelos e dados entre os projetos.
