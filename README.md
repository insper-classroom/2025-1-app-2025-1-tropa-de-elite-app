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
cd front_end
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
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd front_end
npm run dev
```

## Fluxo de Uso do Sistema

### 1. Upload e Processamento de Dados

1. Acesse a página inicial em `http://localhost:3000/`
2. Faça o upload dos três arquivos feather necessários:
   - Arquivo de pagadores (payers.feather)
   - Arquivo de terminais (seller_terminals.feather)
   - Arquivo de transações (transactional_train.feather)
3. Clique em "Fazer Upload" e aguarde a confirmação
4. Após o upload bem-sucedido, clique em "Processar Dados" para preparar os dados para análise
5. O processamento pode levar alguns segundos. Um log de progresso será exibido em tempo real

### 2. Seleção de Modelo

1. Após o processamento dos dados, você será redirecionado para a página de modelos
2. Selecione um dos modelos disponíveis no dropdown
3. O modelo escolhido será utilizado para todas as análises subsequentes

### 3. Análise de Transações Individuais

1. Navegue para "Análise de Transação Única" no menu ou acesse `http://localhost:3000/transacao`
2. Busque transações por card_bin ou filtre por período de data
3. Selecione uma transação da lista de resultados
4. Clique em "Rodar Previsão" para analisar a transação selecionada
5. Os resultados mostrarão se a transação foi classificada como fraude ou não, junto com a probabilidade

### 4. Análise Mensal

1. Navegue para "Análise Mensal" no menu ou acesse `http://localhost:3000/mensal`
2. Confirme o mês para análise (Junho 2024 por padrão)
3. Clique em "Iniciar Análise" para processar todas as transações do mês
4. Após o processamento, visualize estatísticas como:
   - Total de transações
   - Número de fraudes detectadas
   - Taxa de fraude
   - Distribuição de probabilidades

## Recursos Adicionais

### Persistência de Dados

- O sistema mantém o estado entre navegações de página
- Os dados processados e o modelo selecionado são salvos automaticamente
- Você pode reiniciar o navegador e continuar de onde parou

### Verificação de Conectividade

- O sistema verifica automaticamente a conexão com o backend
- Se o backend estiver indisponível, você verá alertas com opções para reconectar
- Todas as páginas de análise exibem o status da conexão backend

### Reset do Sistema

Para limpar todos os dados e começar novamente:

1. Acesse a página inicial
2. Clique no botão "Limpar Dados" no canto inferior da tela
3. Confirme a ação no diálogo de confirmação

## Diagnóstico de Problemas

### Erro de Conexão com o Backend

Se você receber erros de conexão com o backend:

1. Verifique se o servidor backend está em execução em `http://localhost:8000`
2. Confirme que não há erros no terminal onde o backend está rodando
3. Tente clicar no botão "Tentar Reconectar" nos alertas
4. Se o problema persistir, reinicie o backend e recarregue a página

### Erros 404 em Endpoints da API

Se você encontrar erros 404 ao acessar endpoints:

1. Verifique se os caminhos dos arquivos no backend estão corretos
2. Confirme que os dados foram processados corretamente na página inicial
3. Consulte os logs do backend para identificar o problema específico

## Documentação

- Documentação da API: http://localhost:8000/docs
- Arquivos README detalhados estão disponíveis em cada diretório

## Integração com o Projeto de Análise de Dados

Este sistema integra-se com o projeto de análise de dados da equipe, localizado em:
`C:\Users\mateu\OneDrive\Documentos\Quarto_sem\Sprint\2025-1-tropa-de-elite`

A integração é feita através do DVC, que permite o versionamento e compartilhamento dos modelos e dados entre os projetos.
