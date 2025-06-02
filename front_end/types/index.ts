export interface Transaction {
  [key: string]: any; // For additional attributes
}

export interface ModelInfo {
  nome: string;
  variante: string;
  versao: string;
  label: string;
}

export interface PredictionResult {
  prediction: number;
  probability: number;
  features?: Record<string, any>;
  row_index?: number;
}

export interface BatchPredictionResult {
  predictions: number[];
  probabilities: number[];
  threshold: number;
}

export interface ProcessedData {
  message: string;
  output: string;
  head: Record<string, any>[];
  features: string[];
}

export interface SearchResult {
  rows: Record<string, any>[];
  columns: string[];
}

export interface LogsFilter {
  startDate?: Date;
  endDate?: Date;
  modelVersion?: string;
  fraudOnly?: boolean;
}