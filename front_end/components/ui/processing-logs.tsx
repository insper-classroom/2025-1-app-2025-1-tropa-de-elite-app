'use client';

import * as React from 'react';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LogMessage, logStream } from '@/lib/log-stream';

interface ProcessingLogsProps {
  processing: boolean;
}

export function ProcessingLogs({ processing }: ProcessingLogsProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const [active, setActive] = useState(false);
    // Usar logs reais e simulados
  const useMockLogs = true; // Sempre usar mock logs para garantir compatibilidade
  
  useEffect(() => {
    if (!processing) {
      setTimeout(() => setActive(false), 3000); // Esconda após 3 segundos do processamento terminar
      return;
    }
    
    setActive(true);
    setLogs([]);
    
    if (useMockLogs) {
      // Simulação de logs recebidos do backend
      const mockLogs = [
        'Gerando basic features...',
        'Gerando card features...',
        'Normalizando transações do cartão...',
        'Gerando terminal features...',
        'Criando características temporais...',
        'Aplicando transformações...',
        'Preparando dados para o modelo...',
        'Carregando modelo...',
        'Processamento concluído!'
      ];
      
      // Função para simular o recebimento de logs em tempo real
      const simulateLogs = async () => {
        for (let i = 0; i < mockLogs.length && processing; i++) {
          await new Promise(resolve => setTimeout(resolve, 700)); // Espera entre logs
          setLogs(prev => [...prev, mockLogs[i]]);
        }
      };
      
      // Inicia a simulação
      simulateLogs();
    } else {
      // Usar os logs reais via SSE
      const unsubscribe = logStream.subscribe((logMsg: LogMessage) => {
        setLogs(prev => [...prev, logMsg.message]);
      });
      
      return unsubscribe;
    }
  }, [processing, useMockLogs]);
  
  if (!active) return null;
  
  return (
    <Card className="fixed bottom-4 right-4 w-96 shadow-lg z-50 border-blue-500 bg-opacity-95 backdrop-blur-sm">
      <CardHeader className="bg-blue-500 text-white py-2">
        <CardTitle className="text-sm font-medium">Processando dados...</CardTitle>
      </CardHeader>
      <CardContent className="max-h-60 overflow-y-auto p-3">
        <div className="space-y-1 font-mono text-sm">
          {logs.map((log, index) => (
            <div key={index} className="flex">
              <span className="text-blue-500 mr-2">&gt;</span>
              <span>{log}</span>
            </div>
          ))}
          {processing && logs.length > 0 && (
            <div className="flex items-center">
              <span className="text-blue-500 mr-2">&gt;</span>
              <span className="animate-pulse">_</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
