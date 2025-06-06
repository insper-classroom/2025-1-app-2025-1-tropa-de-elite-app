import type { NextApiRequest, NextApiResponse } from 'next';
import { LogsResponse, Transaction } from '@/types';
import { v4 as uuidv4 } from 'uuid';

// Generate mock data for a specific job
const generateMockLogs = (
  jobId: string,
  page: number,
  showRejectedOnly: boolean
): LogsResponse => {
  const itemsPerPage = 10;
  const totalItems = 58; // Total number of transactions for this job
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  
  // Generate deterministic data based on jobId and page
  const seed = jobId + page.toString();
  const random = (min: number, max: number) => {
    const x = Math.sin(seed.charCodeAt(0) + page * 10) * 10000;
    return Math.floor((x - Math.floor(x)) * (max - min + 1) + min);
  };
  
  let logs: Transaction[] = [];
  
  const startItem = (page - 1) * itemsPerPage;
  const endItem = Math.min(startItem + itemsPerPage, totalItems);
  
  for (let i = startItem; i < endItem; i++) {
    const isApproved = (i % 3 !== 0); // Every 3rd transaction is rejected
    
    if (showRejectedOnly && isApproved) {
      continue;
    }
    
    logs.push({
      transactionId: `tx-${jobId.substring(0, 8)}-${i.toString().padStart(4, '0')}`,
      status: isApproved ? 'approved' : 'rejected',
      timestamp: new Date(Date.now() - i * 60000).toISOString(), // Each transaction is 1 minute apart
    });
  }
  
  return {
    logs,
    pagination: {
      currentPage: page,
      totalPages: showRejectedOnly ? Math.ceil(totalItems / 3 / itemsPerPage) : totalPages,
      totalItems: showRejectedOnly ? Math.ceil(totalItems / 3) : totalItems,
      itemsPerPage,
    },
  };
};

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }
  
  const { jobId, page = '1', rejected } = req.query;
  
  if (!jobId || typeof jobId !== 'string') {
    return res.status(400).json({ error: 'Job ID is required' });
  }
  
  const pageNumber = parseInt(page as string, 10) || 1;
  const showRejectedOnly = rejected === 'true';
  
  // Simulate API delay
  setTimeout(() => {
    const response = generateMockLogs(jobId, pageNumber, showRejectedOnly);
    res.status(200).json(response);
  }, 500);
}