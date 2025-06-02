import { BatchPredictionResult, ModelInfo, PredictionResult, ProcessedData, SearchResult } from "@/types";

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

// Enhanced API client with proper error handling and typing
export const api = {
  // Upload files
  uploadFiles: async (payersFile: File, sellersFile: File, transactionsFile: File): Promise<{ message: string; paths: string[] }> => {
    try {
      const formData = new FormData();
      formData.append('payers_file', payersFile);
      formData.append('seller_terminals_file', sellersFile);
      formData.append('transactional_train_file', transactionsFile);
      
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      return handleResponse(response);
    } catch (error) {
      console.error('Error uploading files:', error);
      throw error;
    }
  },

  // Process the uploaded data
  processData: async (): Promise<ProcessedData> => {
    try {
      const response = await fetch(`${API_URL}/process`, {
        method: 'POST',
      });
      return handleResponse(response);
    } catch (error) {
      console.error('Error processing data:', error);
      throw error;
    }
  },

  // Get list of models
  getModels: async (): Promise<ModelInfo[]> => {
    try {
      const response = await fetch(`${API_URL}/modelos`);
      return handleResponse(response);
    } catch (error) {
      console.error('Error fetching models:', error);
      throw error;
    }
  },

  // Search rows in the processed dataset
  searchRows: async (query: string): Promise<SearchResult> => {
    try {
      const response = await fetch(`${API_URL}/search_rows?q=${encodeURIComponent(query)}`);
      return handleResponse(response);
    } catch (error) {
      console.error('Error searching rows:', error);
      throw error;
    }
  },

  // Predict a single row
  predictRow: async (nome: string, variante: string, versao: string, rowIndex: number): Promise<PredictionResult> => {
    try {
      const response = await fetch(`${API_URL}/predict_row?nome=${encodeURIComponent(nome)}&variante=${encodeURIComponent(variante)}&versao=${encodeURIComponent(versao)}&row_index=${rowIndex}`);
      return handleResponse(response);
    } catch (error) {
      console.error('Error predicting row:', error);
      throw error;
    }
  },

  // Predict all rows in the dataset
  predictAll: async (nome: string, variante: string, versao: string): Promise<BatchPredictionResult> => {
    try {
      const response = await fetch(`${API_URL}/predict_all?nome=${encodeURIComponent(nome)}&variante=${encodeURIComponent(variante)}&versao=${encodeURIComponent(versao)}`);
      return handleResponse(response);
    } catch (error) {
      console.error('Error predicting all rows:', error);
      throw error;
    }
  }
};
        body: formData,
      });
      
      return handleResponse(response);
    } catch (error) {
      console.error('Error submitting batch job:', error);
      throw error;
    }
  },

  // Get batch job status with enhanced progress tracking
  getBatchJobStatus: async (jobId: string): Promise<BatchJob> => {
    try {
      const response = await fetch(`${API_URL}/predict/batch/${jobId}/status`);
      return handleResponse(response);
    } catch (error) {
      console.error('Error checking job status:', error);
      throw error;
    }
  },

  // Get logs with filters and proper error handling
  getLogs: async (filters?: LogsFilter): Promise<LogEntry[]> => {
    try {
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

// Development mock data
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  const mockApi = () => {
    const mockTransactions: Record<string, Transaction> = {
      'TX-12345': {
        id: 'TX-12345',
        timestamp: '2023-05-15T10:30:45Z',
        amount: 299.99,
        merchantId: 'MERCH-123',
        customerId: 'CUST-456',
        cardType: 'VISA',
        ipAddress: '192.168.1.1',
        deviceId: 'iPhone-13',
        location: 'New York, USA',
        browser: 'Safari',
        os: 'iOS',
        transactionType: 'mobile',
      },
      'TX-67890': {
        id: 'TX-67890',
        timestamp: '2023-05-16T14:22:33Z',
        amount: 1299.99,
        merchantId: 'MERCH-456',
        customerId: 'CUST-789',
        cardType: 'MASTERCARD',
        ipAddress: '10.0.0.1',
        deviceId: 'Galaxy-S21',
        location: 'Los Angeles, USA',
        browser: 'Chrome',
        os: 'Android',
        transactionType: 'online',
      },
    };

    window.fetch = async (url: string, options?: RequestInit) => {
      const urlObj = new URL(url, window.location.origin);
      const path = urlObj.pathname;

      // Mock current model with DVC info
      if (path === '/api/models/current') {
        return new Response(JSON.stringify({
          version: 'v1.2.3',
          dvcVersion: '1.0.0',
          modelPath: 'models/fraud_detection',
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      if (path.startsWith('/api/predict/transaction/')) {
        const txId = path.split('/').pop() || '';
        
        return new Response(
          JSON.stringify({
            decision: Math.random() > 0.3 ? 'NOT_FRAUD' : 'FRAUD',
            score: Math.random(),
            version: 'v1.2.3',
            timestamp: new Date().toISOString(),
            attributes: mockTransactions[txId] || {},
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }

      if (path === '/api/predict/batch' && options?.method === 'POST') {
        return new Response(
          JSON.stringify({ jobId: `job-${Date.now()}` }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }

      if (path.startsWith('/api/predict/batch/') && path.includes('/status')) {
        const jobId = path.split('/')[3];
        const randomProgress = Math.min(100, Math.floor(Math.random() * 100));
        const status = randomProgress === 100 ? 'completed' : 'processing';
        
        return new Response(
          JSON.stringify({
            jobId,
            progress: randomProgress,
            status,
            downloadUrl: status === 'completed' ? '/api/download/results.csv' : undefined,
            timestamp: new Date().toISOString(),
            userId: 'user-123',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }

      if (path === '/api/logs') {
        const logs: LogEntry[] = Array.from({ length: 20 }, (_, i) => ({
          id: `log-${i}`,
          timestamp: new Date(Date.now() - i * 3600000).toISOString(),
          transactionId: `TX-${10000 + i}`,
          userId: `user-${100 + (i % 5)}`,
          score: Math.random(),
          decision: Math.random() > 0.3 ? 'NOT_FRAUD' : 'FRAUD',
          version: `v1.${Math.floor(i / 5) + 1}.${i % 5}`,
          attributes: {
            amount: Math.random() * 1000,
            merchantId: `MERCH-${Math.floor(Math.random() * 1000)}`,
            cardType: ['VISA', 'MASTERCARD', 'AMEX'][Math.floor(Math.random() * 3)],
          },
        }));
        
        return new Response(
          JSON.stringify(logs),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }

      const originalFetch = window.fetch;
      return originalFetch.call(window, url, options);
    };
  };

  mockApi();
}