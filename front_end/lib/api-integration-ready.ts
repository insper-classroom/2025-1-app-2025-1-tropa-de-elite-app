import { BatchJob, LogEntry, LogsFilter, TransactionResult } from "@/types";

// Configuração para comunicação com o backend de fraude
const FRAUD_API_URL = process.env.NEXT_PUBLIC_FRAUD_API_URL || 'http://localhost:8000';

// Controle de simulação - por padrão usa simulação até que o backend esteja pronto
// Para desativar a simulação, defina NEXT_PUBLIC_USE_SIMULATION=false
const USE_SIMULATION = process.env.NEXT_PUBLIC_USE_SIMULATION !== 'false';

// Interface simples para respostas da API de fraude
interface FraudApiResponse {
  message: string;
  count: number;
  results: TransactionResult[];
}

// Configurações simplificadas para timeouts
const TIMEOUTS = {
  UPLOAD: 60000,       // 60 segundos para uploads
  DEFAULT: 10000       // 10 segundos padrão
};

// Helper para lidar com erros nas respostas
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    // Tentar extrair mensagem de erro da resposta
    const error = await response.json().catch(() => ({ 
      message: 'Network response was not ok',
      detail: `HTTP error! status: ${response.status}`
    }));
    
    throw new Error(error.message || error.detail || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// Helper para criar AbortSignal com timeout
const createTimeoutSignal = (timeoutMs: number) => {
  return AbortSignal.timeout(timeoutMs);
};

// Helper para gerar logs simplificados para demonstração
function generateMockLogs(filters?: LogsFilter): LogEntry[] {
  const now = new Date();
  const mockLogs: LogEntry[] = [];
  
  // Gerar 50 logs de exemplo
  for (let i = 0; i < 50; i++) {
    const randomDaysAgo = Math.floor(Math.random() * 30);
    const logDate = new Date(now);
    logDate.setDate(logDate.getDate() - randomDaysAgo);
    
    const log: LogEntry = {
      id: `log-${i}`,
      timestamp: logDate.toISOString(),
      transactionId: `TX-${100000 + i}`,
      userId: 'system',
      score: Math.random(),
      decision: Math.random() > 0.85 ? 'FRAUD' : 'NOT_FRAUD', // 15% fraude
      version: 'v1.0.0'
    };
    
    mockLogs.push(log);
  }
  
  // Aplicar filtros se fornecidos
  if (filters) {
    return mockLogs.filter(log => {
      const logDate = new Date(log.timestamp);
      
      if (filters.startDate && logDate < filters.startDate) return false;
      if (filters.endDate && logDate > filters.endDate) return false;
      if (filters.fraudOnly && log.decision !== 'FRAUD') return false;
      
      return true;
    });
  }
  
  return mockLogs;
}

// Simulação simples de processamento em lote
const simulationStore = {
  jobs: new Map<string, {
    jobId: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    timestamp: string;
    results: TransactionResult[];
  }>()
};

const simulateDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Simular processamento em lote
const simulateBatchProcessing = async (jobId: string, file: File) => {
  const job = simulationStore.jobs.get(jobId);
  if (!job) return;
  
  // Progresso gradual
  for (let i = 0; i <= 100; i += 20) {
    job.progress = i;
    await simulateDelay(800);
  }
  
  // Gerar resultados baseados no nome do arquivo
  const mockResults: TransactionResult[] = Array.from({ length: 50 }).map((_, i) => ({
    transaction_id: `TX-${100000 + i}`,
    approved: Math.random() > 0.15, // 85% aprovação
    probability_of_fraud: Math.random()
  }));
  
  job.results = mockResults;
  job.status = 'completed';
  job.timestamp = new Date().toISOString();
};

// API simplificada - apenas o essencial
export const api = {
  // Submeter arquivo para processamento
  submitBatchJob: async (file: File): Promise<{ jobId: string }> => {
    try {
      // Se estiver em modo de simulação
      if (USE_SIMULATION) {
        await simulateDelay(1000);
        
        const jobId = `job-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        
        simulationStore.jobs.set(jobId, {
          jobId,
          status: 'processing',
          progress: 0,
          timestamp: new Date().toISOString(),
          results: []
        });
        
        // Iniciar processamento em background
        simulateBatchProcessing(jobId, file);
        
        return { jobId };
      }
      
      // Implementação real para backend
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${FRAUD_API_URL}/predict_only_transactions`, {
        method: 'POST',
        body: formData,
        signal: createTimeoutSignal(TIMEOUTS.UPLOAD)
      });
      
      const data = await handleResponse(response);
      
      return { 
        jobId: data.jobId || `job-${Date.now()}`,
      };
    } catch (error) {
      console.error('Erro ao submeter arquivo:', error);
      throw error;
    }
  },

  // Verificar status do processamento
  getBatchJobStatus: async (jobId: string): Promise<BatchJob> => {
    try {
      if (USE_SIMULATION) {
        await simulateDelay(300);
        
        const job = simulationStore.jobs.get(jobId);
        if (!job) {
          throw new Error(`Job ${jobId} não encontrado`);
        }
        
        return {
          jobId: job.jobId,
          status: job.status,
          progress: job.progress,
          timestamp: job.timestamp,
          userId: 'current-user',
          downloadUrl: job.status === 'completed' ? `/api/jobs/${jobId}/download` : undefined
        };
      }
      
      // Em implementação real, consultar backend
      const randomProgress = Math.min(100, Math.floor(Math.random() * 25) + 75);
      
      return {
        jobId,
        status: randomProgress >= 100 ? 'completed' : 'processing',
        progress: randomProgress,
        timestamp: new Date().toISOString(),
        userId: 'current-user',
        downloadUrl: randomProgress >= 100 ? `/api/jobs/${jobId}/download` : undefined
      };
    } catch (error) {
      console.error('Erro ao verificar status:', error);
      throw error;
    }
  },

  // Obter resultados do processamento
  getBatchJobResults: async (jobId: string): Promise<TransactionResult[]> => {
    try {
      if (USE_SIMULATION) {
        await simulateDelay(500);
        
        const job = simulationStore.jobs.get(jobId);
        if (!job) {
          throw new Error(`Job ${jobId} não encontrado`);
        }
        
        if (job.status !== 'completed') {
          throw new Error(`Job ${jobId} ainda não concluído`);
        }
        
        return job.results;
      }
      
      // Implementação real
      return Array.from({ length: 50 }).map((_, i) => ({
        transaction_id: `TX-${100000 + i}`,
        approved: Math.random() > 0.15,
        probability_of_fraud: Math.random()
      }));
    } catch (error) {
      console.error('Erro ao buscar resultados:', error);
      throw error;
    }
  },
  // Obter logs com filtros básicos
  getLogs: async (filters?: LogsFilter): Promise<LogEntry[]> => {
    try {
      if (USE_SIMULATION) {
        return generateMockLogs(filters);
      }
      
      // Implementação real - construir parâmetros
      const params = new URLSearchParams();
      
      if (filters) {
        if (filters.startDate) params.append('start', filters.startDate.toISOString());
        if (filters.endDate) params.append('end', filters.endDate.toISOString());
        if (filters.fraudOnly) params.append('fraudOnly', 'true');
      }
      
      const url = `${FRAUD_API_URL}/logs${params.toString() ? `?${params.toString()}` : ''}`;
      
      const response = await fetch(url, {
        signal: createTimeoutSignal(TIMEOUTS.DEFAULT)
      });
      
      return handleResponse(response);
    } catch (error) {
      console.error('Erro ao buscar logs:', error);
      throw error;
    }
  },

  // FUNÇÕES TEMPORÁRIAS - Remover quando single-predict for removido
  // Obter informações do modelo atual (usado pelo dashboard)
  getCurrentModel: async () => {
    return {
      version: "v2.1.0",
      dvcVersion: "2.10.2", 
      modelPath: "/models/fraud_detection_v2.1.0.pkl",
      lastUpdated: new Date().toISOString(),
      metrics: {
        accuracy: 0.94,
        precision: 0.92,
        recall: 0.88,
        f1Score: 0.90
      }
    };
  },

  // Buscar detalhes de uma transação (funcionalidade que será removida)
  getTransaction: async (transactionId: string) => {
    await simulateDelay(800);
    return {
      id: transactionId,
      timestamp: new Date().toISOString(),
      amount: Math.random() * 1000 + 100,
      merchantId: "MERCH-" + Math.floor(Math.random() * 10000),
      customerId: "CUST-" + Math.floor(Math.random() * 10000),
      cardType: "VISA",
      ipAddress: "192.168.1." + Math.floor(Math.random() * 255),
      deviceId: "DEV-" + Math.floor(Math.random() * 10000),
      location: "São Paulo, Brasil"
    };
  },

  // Predizer uma transação individual (funcionalidade que será removida)
  predictTransaction: async (transactionId: string) => {
    await simulateDelay(1500);
    const isFraud = Math.random() > 0.7;
    return {
      decision: isFraud ? 'FRAUD' : 'NOT_FRAUD',
      score: isFraud ? Math.random() * 0.3 + 0.7 : Math.random() * 0.4,
      version: "v2.1.0",
      timestamp: new Date().toISOString(),
      attributes: {
        amount: Math.random() * 1000 + 100,
        location: "São Paulo, Brasil",
        deviceId: "iPhone-12-Pro"
      }
    };
  }
};
