import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;
    const modelId = formData.get('modelId') as string | null;

    if (!file || !modelId) {
      return NextResponse.json(
        { error: 'File and modelId are required' },
        { status: 400 }
      );
    }

    // Check if file is a CSV
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return NextResponse.json(
        { error: 'Only CSV files are supported' },
        { status: 400 }
      );
    }

    // In a real application, you would process the file and send it to a model service
    // Here we're just generating a random job ID
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Generate random jobId
    const jobId = `job-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    return NextResponse.json({ jobId });
  } catch (error) {
    console.error('Error processing batch prediction:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
}