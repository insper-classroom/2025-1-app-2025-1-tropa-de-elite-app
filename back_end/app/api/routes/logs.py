from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
import logging
import sys

# Configuração do router
router = APIRouter()

# Buffer para logs recentes
recent_logs = []
MAX_LOGS = 100

# Handler personalizado para capturar logs
class BufferHandler(logging.Handler):
    def emit(self, record):
        global recent_logs
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": self.format(record)
        }
        recent_logs.append(log_entry)
        # Manter apenas os logs mais recentes
        if len(recent_logs) > MAX_LOGS:
            recent_logs = recent_logs[-MAX_LOGS:]

# Adicionar handler ao logger root
handler = BufferHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(handler)

# Lista de conexões ativas
connections = set()

async def notify_clients(message):
    """Notifica todas as conexões ativas sobre um novo log."""
    for queue in list(connections):
        await queue.put(message)

# Endpoint para stream de eventos
@router.get("/stream")
async def stream(request: Request):
    """Stream de logs em tempo real usando Server-Sent Events."""
    client_queue = asyncio.Queue()
    connections.add(client_queue)
    
    # Enviar logs recentes para o novo cliente
    for log in recent_logs:
        await client_queue.put(log)
    
    async def event_generator() -> AsyncGenerator[bytes, None]:
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                # Esperar por novo log ou timeout após 1 segundo
                try:
                    log = await asyncio.wait_for(client_queue.get(), 1)
                    yield f"data: {json.dumps(log)}\n\n".encode('utf-8')
                except asyncio.TimeoutError:
                    # Enviar heartbeat para manter a conexão
                    yield f": heartbeat\n\n".encode('utf-8')
        finally:
            connections.remove(client_queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

# Rota para obter logs recentes
@router.get("/recent")
async def get_recent_logs():
    """Obter logs recentes."""
    return recent_logs
