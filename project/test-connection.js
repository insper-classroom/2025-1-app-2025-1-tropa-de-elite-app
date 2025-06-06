// Test script to verify backend connection
import { getModels, processBatch } from './src/services/api.js';

async function testConnection() {
  console.log('🔄 Testing connection to FastAPI backend...');
  
  try {
    // Test 1: Get models (mock data since backend doesn't have this route)
    console.log('📋 Testing getModels...');
    const models = await getModels();
    console.log('✅ Models fetched:', models);
    
    // Test 2: Create a dummy file for batch processing
    console.log('📁 Testing file upload simulation...');
    const dummyFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
    
    try {
      await processBatch(dummyFile, 'model-1');
      console.log('✅ Backend connection successful!');
    } catch (error) {
      if (error.message.includes('Network Error') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        console.log('❌ Backend is not running. Please start the FastAPI server first.');
        console.log('💡 Run: cd back_end && python api/app.py');
      } else {
        console.log('⚠️  Backend is running but returned an error:', error.message);
        console.log('💡 This might be expected if you haven\'t uploaded the required model files yet.');
      }
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Only run if this is the main module
if (typeof window === 'undefined') {
  testConnection();
}

export { testConnection };
