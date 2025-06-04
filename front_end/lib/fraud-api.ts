// Configuração para comunicação com o backend de fraude
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Controle de simulação - por padrão usa simulação até que o backend esteja pronto
// Para desativar a simulação, defina NEXT_PUBLIC_USE_SIMULATION=false
const USE_SIMULATION = process.env.NEXT_PUBLIC_USE_SIMULATION !== 'false';

// Interfaces para resultados e requests
interface TransactionResult {
  transaction_id: string;
  approved: boolean;
  probability_of_fraud: number;
}

interface FraudApiResponse {
  message: string;
  count: number;
  results: TransactionResult[];
}

interface ApiError {
  detail: string;
  status: number;
  title?: string;
}

// Simulação para desenvolvimento sem backend
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

// Simulação de processamento em lote
const simulateBatchProcessing = async (jobId: string, file: File) => {
  const job = simulationStore.jobs.get(jobId);
  if (!job) return;
  
  // Simulação de progresso
  for (let i = 0; i <= 100; i += 10) {
    job.progress = i;
    await simulateDelay(500);
  }
  
  // Gerar resultados simulados
  const mockResults: TransactionResult[] = Array.from({ length: 537 }).map((_, i) => ({
    transaction_id: `TX-${100000 + i}`,
    approved: Math.random() > 0.15, // 15% de rejeição
    probability_of_fraud: Math.random()
  }));
  
  job.results = mockResults;
  job.status = 'completed';
  job.timestamp = new Date().toISOString();
};

// API para comunicação com o backend de detecção de fraudes
export const fraudApi = {
  // Submeter um arquivo CSV para processamento de transações
  submitTransactionsFile: async (file: File): Promise<FraudApiResponse> => {
    // If in simulation mode, create a batch job and return simulated results
    if (USE_SIMULATION) {
      const { jobId } = await fraudApi.submitBatchJob(file);
      await simulateDelay(2000); // Wait for simulated processing
      const results = await fraudApi.getBatchJobResults(jobId);
      return {
        message: `Predição concluída: ${results.length} registros`,
        count: results.length,
        results
      };
    }
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_URL}/predict_only_transactions`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(30000) // 30 segundos de timeout para arquivos grandes
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error: ApiError = {
          detail: errorData.detail || `Erro ${response.status}: Falha ao processar transações`,
          status: response.status,
          title: 'Erro de processamento'
        };
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      console.error('Erro ao enviar arquivo de transações:', error);
      if ((error as ApiError).status) {
        throw error;
      }
      throw {
        detail: error instanceof Error ? error.message : 'Erro desconhecido ao processar transações',
        status: 500,
        title: 'Erro de conexão'
      };
    }
  },
    // Verificar o status do servidor/API
  checkHealth: async (): Promise<{ status: string; database: string; files?: any; memory?: any }> => {
    if (USE_SIMULATION) {
      return {
        status: 'ok',
        database: 'simulated',
        files: {
          model: 'simulated',
          dataset: 'simulated'
        },
        memory: {
          dataset_loaded: true,
          model_loaded: true
        }
      };
    }
    
    try {
      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        },
        // Adicionar um timeout para evitar que a requisição fique pendente indefinidamente
        signal: AbortSignal.timeout(5000)
      });
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Sem detalhes');
        throw new Error(`Erro ${response.status}: Serviço indisponível - ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Erro ao verificar status do servidor:', error);
      throw {
        detail: error instanceof Error ? error.message : 'Erro desconhecido ao verificar status',
        status: 500,
        title: 'Erro de conexão'
      };
    }
  },
  
  // Submeter um job em lote (simulação para desenvolvimento)
  submitBatchJob: async (file: File): Promise<{ jobId: string }> => {
    try {
      // Simulação de delay na API
      await simulateDelay(1000);
      
      // Gerar ID de job aleatório
      const jobId = `job-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
      
      // Criar job simulado
      simulationStore.jobs.set(jobId, {
        jobId,
        status: 'processing',
        progress: 0,
        timestamp: new Date().toISOString(),
        results: []
      });
      
      // Iniciar processamento simulado
      simulateBatchProcessing(jobId, file);
      
      return { jobId };
    } catch (error) {
      console.error('Erro ao submeter processamento em lote:', error);
      throw error;
    }
  },
  
  // Obter status de um job em lote (simulação)
  getBatchJobStatus: async (jobId: string) => {
    try {
      // Simulação de delay na API
      await simulateDelay(500);
      
      const job = simulationStore.jobs.get(jobId);
      if (!job) {
        throw new Error(`Job com ID ${jobId} não encontrado`);
      }
      
      return {
        jobId: job.jobId,
        status: job.status,
        progress: job.progress,
        timestamp: job.timestamp,
        userId: 'current-user',
        downloadUrl: job.status === 'completed' ? `/api/download/${jobId}` : undefined
      };
    } catch (error) {
      console.error('Erro ao verificar status do job:', error);
      throw error;
    }
  },
  
  // Obter resultados de um job concluído (simulação)
  getBatchJobResults: async (jobId: string): Promise<TransactionResult[]> => {
    try {
      // Simulação de delay na API
      await simulateDelay(700);
      
      const job = simulationStore.jobs.get(jobId);
      if (!job) {
        throw new Error(`Job com ID ${jobId} não encontrado`);
      }
      
      if (job.status !== 'completed') {
        throw new Error(`Job com ID ${jobId} ainda não foi concluído`);
      }
      
      return job.results;
    } catch (error) {
      console.error('Erro ao buscar resultados do job:', error);
      throw error;
    }
  }
};
