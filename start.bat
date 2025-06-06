@echo off
REM Script para iniciar o backend e o frontend em paralelo

echo Iniciando sistema de detecção de fraudes...

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python não encontrado. Por favor, instale Python 3.9+.
    exit /b 1
)

REM Verifica se Node.js está instalado
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js não encontrado. Por favor, instale Node.js.
    exit /b 1
)

REM Inicia o backend
echo Iniciando backend...
cd back_end
pip install -r requirements.txt
uvicorn main:app --reload

REM Inicia o frontend
echo Iniciando frontend...
cd front_end
npm install
npm run dev

echo.
echo Sistema iniciado! Acesse:
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo Backend Docs: http://localhost:8000/docs
echo.
echo Pressione qualquer tecla para encerrar todos os processos...

pause >nul

REM Encerra todos os processos
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

echo Sistema encerrado.
