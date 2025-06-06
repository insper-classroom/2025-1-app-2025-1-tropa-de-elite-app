export interface Model {
  id: string;
  name: string;
  version: string;
  createdAt: string;
}

export interface Transaction {
  transactionId: string;
  status: 'approved' | 'rejected';
  timestamp: string;
}

export interface LogsResponse {
  logs: Transaction[];
  pagination: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    itemsPerPage: number;
  };
}

export interface BatchResponse {
  jobId: string;
  message: string;
}