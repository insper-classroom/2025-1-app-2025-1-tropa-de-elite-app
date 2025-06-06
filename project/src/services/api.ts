import axios from 'axios';
import { Model, LogsResponse, BatchResponse } from '@/types';

// Base URL for the FastAPI backend
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  (process.env.NODE_ENV === 'production' 
    ? 'http://YOUR_EC2_IP:8000'  // Replace with your actual EC2 IP
    : 'http://localhost:8000');

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Configure for large file uploads
  timeout: 300000, // 5 minutes timeout for large files
  maxContentLength: 104857600, // 100MB
  maxBodyLength: 104857600, // 100MB
});

export const getModels = async (): Promise<Model[]> => {
  try {
    // Backend doesn't have this route, so return mock data
    return [{
      id: 'model-1',
      name: 'Fraud Detection Model',
      version: 'v1.0.0',
      createdAt: new Date().toISOString()
    }];
  } catch (error) {
    console.error('Error fetching models:', error);
    throw error;
  }
};

export const processBatch = async (
  file: File, 
  modelId: string, 
  onUploadProgress?: (progressEvent: any) => void
): Promise<BatchResponse> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    // Use the actual backend route
    const response = await api.post<BatchResponse>('/predict_batch_file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Add upload progress tracking
      onUploadProgress: onUploadProgress ? (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress({ progress: percentCompleted });
        }
      } : undefined,
      // Extend timeout for large files
      timeout: 600000, // 10 minutes for batch processing
    });
    
    return response.data;
  } catch (error) {
    console.error('Error processing batch:', error);
    throw error;
  }
};

export const getLogs = async (jobId: string, page: number, showRejectedOnly?: boolean): Promise<LogsResponse> => {
  try {
    // Backend doesn't have this specific route, return mock data
    const mockLogs = Array.from({ length: 10 }, (_, i) => ({
      transactionId: `TX-${10000 + i}`,
      status: (Math.random() > 0.7 ? 'rejected' : 'approved') as 'rejected' | 'approved',
      timestamp: new Date(Date.now() - i * 3600000).toISOString(),
    }));

    return {
      logs: showRejectedOnly ? mockLogs.filter(log => log.status === 'rejected') : mockLogs,
      pagination: {
        currentPage: page,
        totalPages: 5,
        totalItems: 50,
        itemsPerPage: 10,
      }
    };
  } catch (error) {
    console.error('Error fetching logs:', error);
    throw error;
  }
};

// Remove single transaction prediction as backend doesn't support it
export const predictTransaction = async (transactionId: string) => {
  // Backend doesn't have this route, return mock data
  return {
    transactionId,
    prediction: Math.random() > 0.7 ? 'fraud' : 'legitimate',
    confidence: Math.random(),
    timestamp: new Date().toISOString(),
  };
};