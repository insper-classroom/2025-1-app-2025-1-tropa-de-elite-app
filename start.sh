#!/bin/bash
# Script para iniciar o backend e o frontend em paralelo

echo "Iniciando sistema de detecção de fraudes..."

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python não encontrado. Por favor, instale Python 3.9+."
    exit 1
fi

# Verifica se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "Node.js não encontrado. Por favor, instale Node.js."
    exit 1
fi

# Inicia o backend
echo "Iniciando backend..."
cd back_end && python3 -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Inicia o frontend
echo "Iniciando frontend..."
cd front_end && npm run dev &
FRONTEND_PID=$!

echo ""
echo "Sistema iniciado! Acesse:"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Backend Docs: http://localhost:8000/docs"
echo ""
echo "Pressione CTRL+C para encerrar todos os processos..."

# Captura CTRL+C para encerrar processos
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Aguarda
wait
