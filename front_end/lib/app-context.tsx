'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ModelInfo, ProcessedData } from '@/types';
import { api } from '@/lib/api-clean';

interface AppState {
  // Dados carregados
  files: {
    payers: File | null;
    seller_terminals: File | null;
    transactional_train: File | null;
  };
  uploadSuccess: boolean;
  processedData: ProcessedData | null;
  
  // Status de processamento
  loading: boolean;
  processing: boolean;
  error: string | null;
  
  // Modelos
  models: ModelInfo[];
  selectedModel: ModelInfo | null;
  
  // Ações
  setFiles: (field: string, file: File | null) => void;
  uploadFiles: () => Promise<boolean>;
  processData: () => Promise<boolean>;
  setSelectedModel: (model: ModelInfo | null) => void;
  resetError: () => void;
  resetState: () => void;
}

const initialState: AppState = {
  files: {
    payers: null,
    seller_terminals: null,
    transactional_train: null
  },
  uploadSuccess: false,
  processedData: null,
  loading: false,
  processing: false,
  error: null,
  models: [],
  selectedModel: null,
  setFiles: () => {},
  uploadFiles: async () => false,
  processData: async () => false,
  setSelectedModel: () => {},
  resetError: () => {},
  resetState: () => {}
};

const AppContext = createContext<AppState>(initialState);

export function AppProvider({ children }: { children: ReactNode }) {
  const [files, setFilesState] = useState<{
    payers: File | null;
    seller_terminals: File | null;
    transactional_train: File | null;
  }>(initialState.files);
  
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  
  // Carregar modelos quando o componente montar
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await api.getModels();
        setModels(data);
      } catch (err) {
        console.error('Erro ao carregar modelos:', err);
      }
    };
    
    fetchModels();
    
    // Carregar estado salvo do localStorage, se existir
    const loadSavedState = () => {
      try {
        // Carregar modelo selecionado
        const savedModel = localStorage.getItem('selectedModel');
        if (savedModel) {
          setSelectedModel(JSON.parse(savedModel));
        }
        
        // Carregar dados processados
        const savedProcessedData = localStorage.getItem('processedData');
        if (savedProcessedData) {
          setProcessedData(JSON.parse(savedProcessedData));
        }
        
        // Carregar status de upload
        const savedUploadSuccess = localStorage.getItem('uploadSuccess');
        if (savedUploadSuccess) {
          setUploadSuccess(JSON.parse(savedUploadSuccess));
        }
      } catch (err) {
        console.error('Erro ao carregar estado salvo:', err);
      }
    };
    
    loadSavedState();
  }, []);
  
  // Salvar estado no localStorage quando mudar
  useEffect(() => {
    if (selectedModel) {
      localStorage.setItem('selectedModel', JSON.stringify(selectedModel));
    }
  }, [selectedModel]);
  
  useEffect(() => {
    if (processedData) {
      localStorage.setItem('processedData', JSON.stringify(processedData));
    }
  }, [processedData]);
  
  useEffect(() => {
    localStorage.setItem('uploadSuccess', JSON.stringify(uploadSuccess));
  }, [uploadSuccess]);
  
  // Função para definir arquivos
  const setFiles = (field: string, file: File | null) => {
    setFilesState(prev => ({
      ...prev,
      [field]: file
    }));
  };
  
  // Função para fazer upload de arquivos
  const uploadFiles = async (): Promise<boolean> => {
    if (!files.payers || !files.seller_terminals || !files.transactional_train) {
      setError('Por favor, selecione todos os arquivos feather');
      return false;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      await api.uploadFiles(
        files.payers,
        files.seller_terminals,
        files.transactional_train
      );
      
      setUploadSuccess(true);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar o upload');
      setUploadSuccess(false);
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  // Função para processar dados
  const processData = async (): Promise<boolean> => {
    try {
      setProcessing(true);
      setError(null);
      
      const data = await api.processData();
      setProcessedData(data);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar os dados');
      return false;
    } finally {
      setProcessing(false);
    }
  };
    // Função para resetar erro
  const resetError = () => setError(null);
  
  // Função para resetar todo o estado
  const resetState = () => {
    setFilesState({
      payers: null,
      seller_terminals: null,
      transactional_train: null
    });
    setUploadSuccess(false);
    setProcessedData(null);
    setSelectedModel(null);
    setError(null);
    
    // Limpar localStorage
    localStorage.removeItem('selectedModel');
    localStorage.removeItem('processedData');
    localStorage.removeItem('uploadSuccess');
  };
  
  const value = {
    files,
    uploadSuccess,
    processedData,
    loading,
    processing,
    error,
    models,
    selectedModel,
    setFiles,
    uploadFiles,
    processData,
    setSelectedModel,
    resetError,
    resetState
  };
  
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useAppState = () => useContext(AppContext);
