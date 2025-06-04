'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import FileUploader from '@/components/file-uploader';
import ModelSelect from '@/components/model-select';
import { Button } from '@/components/ui/button';
import { submitPrediction } from '@/lib/api';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [modelId, setModelId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const handleFileSelected = (selectedFile: File) => {
    setFile(selectedFile);
  };

  const handleModelSelect = (selectedModelId: string) => {
    setModelId(selectedModelId);
  };

  const handleSubmit = async () => {
    if (!file || !modelId) {
      toast({
        title: "Informações faltando",
        description: "Por favor, selecione um arquivo e um modelo",
        variant: "destructive",
      });
      return;
    }

    try {
      setLoading(true);
      const response = await submitPrediction(file, modelId);
      
      if (response.jobId) {
        toast({
          title: "Sucesso!",
          description: "Seu trabalho foi enviado com sucesso",
        });
        router.push(`/logs/${response.jobId}`);
      }
    } catch (error) {
      console.error('Erro ao enviar predição:', error);
      toast({
        title: "Erro",
        description: "Falha ao enviar o trabalho. Por favor, tente novamente.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">Processador de Transações</h1>
          <p className="text-muted-foreground mt-2">
            Faça upload de um arquivo CSV e selecione um modelo para analisar suas transações
          </p>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold">Upload de Transações</h2>
            <FileUploader 
              onFileSelected={handleFileSelected}
              className="h-48"
            />
            {file && (
              <p className="text-sm text-green-600">
                Selecionado: {file.name}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <h2 className="text-lg font-semibold">Selecionar Versão do Modelo</h2>
            <ModelSelect 
              onModelSelect={handleModelSelect} 
              disabled={loading}
            />
          </div>

          <Button
            className="w-full"
            size="lg"
            onClick={handleSubmit}
            disabled={!file || !modelId || loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processando...
              </>
            ) : (
              'Executar Modelo'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}