import { NextResponse } from 'next/server';

// Mock data for models
// In a real application, this would come from a database or external service
const models = [
  { id: 'model-1', name: 'Fraud Detection', version: '1.0.0' },
  { id: 'model-2', name: 'Fraud Detection', version: '1.1.0' },
  { id: 'model-3', name: 'Transaction Risk', version: '2.0.0' },
  { id: 'model-4', name: 'Compliance Check', version: '1.0.0' },
];

export async function GET() {
  // Add artificial delay to simulate network latency
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return NextResponse.json(models);
}