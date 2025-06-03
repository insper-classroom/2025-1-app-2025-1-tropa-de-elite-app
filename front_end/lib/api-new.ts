// filepath: c:\Users\mateu\OneDrive\Documentos\Quarto_sem\Sprint\2025-1-app-2025-1-tropa-de-elite-app\front_end\lib\api.ts
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
export const api = {  // Upload files
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
