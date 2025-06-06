import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import FileUploader from '@/components/ui/FileUploader';
import ModelSelect from '@/components/ui/ModelSelect';
import Button from '@/components/ui/Button';
import { getModels, processBatch } from '@/services/api';
import { Model } from '@/types';

export default function Home() {
  const router = useRouter();
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const modelsData = await getModels();
        setModels(modelsData);
        if (modelsData.length > 0) {
          setSelectedModel(modelsData[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch models:', err);
        setError('Não foi possível carregar os modelos disponíveis. Por favor, tente novamente.');
      } finally {
        setIsLoadingModels(false);
      }
    };

    fetchModels();
  }, []);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
  };

  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId);
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError('Por favor, selecione um arquivo.');
      return;
    }

    if (!selectedModel) {
      setError('Por favor, selecione um modelo.');
      return;
    }

    setError(null);
    setIsLoading(true);
    setUploadProgress(0);

    try {
      const response = await processBatch(selectedFile, selectedModel, (progress) => {
        setUploadProgress(progress);
      });
      router.push(`/logs/${response.jobId}`);
    } catch (err) {
      console.error('Failed to process batch:', err);
      setError('Ocorreu um erro ao processar o lote. Por favor, tente novamente.');
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h1 className="text-lg font-medium leading-6 text-gray-900">
            Processamento de Transações
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Faça upload de um arquivo CSV, Feather ou Parquet contendo transações para processamento (máx. 100MB).
          </p>

          <div className="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
            <div className="sm:col-span-6">
              <FileUploader onFileSelect={handleFileSelect} />
            </div>

            <div className="sm:col-span-6 sm:flex sm:items-end sm:space-x-4">
              <div className="flex-grow">
                <ModelSelect 
                  models={models}
                  selectedModel={selectedModel}
                  onSelect={handleModelSelect}
                  isLoading={isLoadingModels}
                />
              </div>
              <div className="mt-4 sm:mt-0">
                <Button
                  onClick={handleSubmit}
                  disabled={!selectedFile || !selectedModel || isLoading}
                  loading={isLoading}
                >
                  {isLoading ? 'Processando...' : 'Rodar Modelo'}
                </Button>
              </div>
            </div>

            {isLoading && uploadProgress > 0 && (
              <div className="sm:col-span-6">
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                    <span>Enviando arquivo...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md">
              <p className="text-sm">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}