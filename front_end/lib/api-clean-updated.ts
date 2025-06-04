import { BatchJob, LogEntry, LogsFilter, ModelInfo, PredictionResult, Transaction } from "@/types";

// Base API URL - configurable through environment
const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

// Helper for handling response errors with better error messages
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Network response was not ok' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// Helper function to generate mock logs with date filtering
function generateMockLogs(filters?: LogsFilter): LogEntry[] {
  // Create a date range from the last 30 days
  const now = new Date();
  const mockLogs: LogEntry[] = [];
  
  // Generate 100 random logs
  for (let i = 0; i < 100; i++) {
    const randomDaysAgo = Math.floor(Math.random() * 30);
    const logDate = new Date(now);
    logDate.setDate(logDate.getDate() - randomDaysAgo);
    
    const log: LogEntry = {
      id: `log-${i}`,
      timestamp: logDate.toISOString(),
      transactionId: `TX-${100000 + i}`,
      userId: `user-${1000 + Math.floor(Math.random() * 50)}`,
      score: Math.random(),
      decision: Math.random() > 0.8 ? 'FRAUD' : 'NOT_FRAUD',
      version: ['v1.0.0', 'v1.1.0', 'v1.2.0', 'v1.2.3'][Math.floor(Math.random() * 4)],
      attributes: {
        amount: Math.floor(Math.random() * 1000) + 10,
        merchantCountry: ['BR', 'US', 'AR', 'CL', 'MX'][Math.floor(Math.random() * 5)],
        cardType: ['VISA', 'MASTERCARD', 'AMEX'][Math.floor(Math.random() * 3)],
        isNewDevice: Math.random() > 0.7,
        deviceType: ['mobile', 'desktop', 'tablet'][Math.floor(Math.random() * 3)]
      }
    };
    
    mockLogs.push(log);
  }
  
  // Apply filters if provided
  if (filters) {
    return mockLogs.filter(log => {
      const logDate = new Date(log.timestamp);
      
      // Filter by date range
      if (filters.startDate && logDate < filters.startDate) {
        return false;
      }
      
      if (filters.endDate && logDate > filters.endDate) {
        return false;
      }
      
      // Filter by model version
      if (filters.modelVersion && log.version !== filters.modelVersion) {
        return false;
      }
      
      // Filter by fraud status
      if (filters.fraudOnly && log.decision !== 'FRAUD') {
        return false;
      }
      
      return true;
    });
  }
  
  return mockLogs;
}

// Enhanced API client with proper error handling and typing
export const api = {
  // Get current model information with version tracking
  getCurrentModel: async (): Promise<ModelInfo> => {
    try {
      const response = await fetch(`${API_URL}/models/current`);
      const data = await handleResponse(response);
      return {
        ...data,
        // Add DVC-specific information if available
        dvcVersion: data.dvcVersion,
        modelPath: data.modelPath,
      };
    } catch (error) {
      console.error('Error fetching model info:', error);
      throw error;
    }
  },

  // Get transaction by ID with enhanced error handling
  getTransaction: async (id: string): Promise<Transaction> => {
    try {
      const response = await fetch(`${API_URL}/transactions/${id}`);
      return handleResponse(response);
    } catch (error) {
      console.error('Error fetching transaction:', error);
      throw error;
    }
  },

  // Predict transaction fraud with model versioning
  predictTransaction: async (id: string): Promise<PredictionResult> => {
    try {
      const response = await fetch(`${API_URL}/predict/transaction/${id}`);
      return handleResponse(response);
    } catch (error) {
      console.error('Error predicting transaction:', error);
      throw error;
    }
  },
  
  // Submit batch prediction job with progress tracking
  submitBatchJob: async (file: File): Promise<{ jobId: string }> => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Usar o endpoint do nosso backend
      const response = await fetch(`${API_URL}/predict_only_transactions`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await handleResponse(response);
      
      // Adaptar o formato da resposta para o esperado pelo frontend
      return { 
        jobId: `job-${Date.now()}`, // Criar um ID temporário para o job
        // O backend real deveria retornar um jobId apropriado
      };
    } catch (error) {
      console.error('Error submitting batch job:', error);
      throw error;
    }
  },

  // Get batch job status with enhanced progress tracking
  getBatchJobStatus: async (jobId: string): Promise<BatchJob> => {
    try {
      // Simular progresso do processamento
      // Em uma implementação real, consultaria o status do job no backend
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
      console.error('Error checking job status:', error);
      throw error;
    }
  },

  // Get logs with filters and proper error handling
  getLogs: async (filters?: LogsFilter): Promise<LogEntry[]> => {
    try {
      // For development, simulate filtering by dates
      if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
        // Return mock data with date filtering
        return generateMockLogs(filters);
      }
      
      const params = new URLSearchParams();
      
      if (filters) {
        if (filters.startDate) params.append('start', filters.startDate.toISOString());
        if (filters.endDate) params.append('end', filters.endDate.toISOString());
        if (filters.modelVersion) params.append('model', filters.modelVersion);
        if (filters.fraudOnly) params.append('fraudOnly', 'true');
      }
      
      const url = `${API_URL}/logs${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await fetch(url);
      return handleResponse(response);
    } catch (error) {
      console.error('Error fetching logs:', error);
      throw error;
    }
  },
};
