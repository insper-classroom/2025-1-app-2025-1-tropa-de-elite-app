import type { NextApiRequest, NextApiResponse } from 'next';
import { Model } from '@/types';

// Mocked data for models
const mockModels: Model[] = [
  {
    id: 'model-1',
    name: 'Random Forest',
    version: '1.0.0',
    createdAt: '2023-01-15T10:30:00Z',
  },
  {
    id: 'model-2',
    name: 'XGBoost',
    version: '2.1.3',
    createdAt: '2023-03-22T14:15:30Z',
  },
  {
    id: 'model-3',
    name: 'Neural Network',
    version: '0.9.5',
    createdAt: '2023-05-08T09:45:12Z',
  },
];

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<Model[]>
) {
  if (req.method === 'GET') {
    // Simulate API delay
    setTimeout(() => {
      res.status(200).json(mockModels);
    }, 500);
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}