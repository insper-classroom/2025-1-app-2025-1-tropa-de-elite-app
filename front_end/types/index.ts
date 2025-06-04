export interface Transaction {
  id: string;
  timestamp: string;
  amount: number;
  merchantId: string;
  customerId: string;
  cardType: string;
  ipAddress: string;
  deviceId: string;
  location: string;
  [key: string]: any; // For additional attributes
}

export interface PredictionResult {
  decision: 'FRAUD' | 'NOT_FRAUD';
  score: number;
  version: string;
  timestamp: string;
  attributes: Record<string, any>;
}

export interface BatchJob {
  jobId: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
  timestamp: string;
  userId: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  transactionId: string;
  userId: string;
  score: number;
  decision: 'FRAUD' | 'NOT_FRAUD';
  version: string;
  attributes?: Record<string, any>;
}

export interface TransactionResult {
  transaction_id: string;
  approved: boolean;
  probability_of_fraud: number;
}

export interface ModelInfo {
  version: string;
  dvcVersion?: string;
  modelPath?: string;
  lastUpdated?: string;
  metrics?: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1Score?: number;
  };
}

export interface LogsFilter {
  startDate?: Date;
  endDate?: Date;
  modelVersion?: string;
  fraudOnly?: boolean;
}