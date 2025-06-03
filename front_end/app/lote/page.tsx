'use client';

import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = ['.csv', '.json'];

export default function LotePage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): boolean => {
    const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!ALLOWED_FILE_TYPES.includes(extension)) {
      setError(`Tipo de arquivo não suportado. Use apenas ${ALLOWED_FILE_TYPES.join(', ')}`);
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError(`Arquivo muito grande. Tamanho máximo: ${MAX_FILE_SIZE / 1024 / 1024}MB`);
      return false;
    }

    return true;
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
      } else {
        e.target.value = ''; // Limpa o input
        setFile(null);
      }
    }
  }, [validateFile]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/analise/lote', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setResultado(url);
    } catch (error) {
      console.error('Erro ao processar lote:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar o arquivo');
    } finally {
      setLoading(false);
    }
  }, [file]);

  const handleDownload = useCallback(() => {
    if (resultado) {
      window.open(resultado);
    }
  }, [resultado]);

  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle>Processamento em Lote</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="arquivo">Arquivo de Transações (CSV/JSON)</Label>
              <input
                id="arquivo"
                type="file"
                accept={ALLOWED_FILE_TYPES.join(',')}
                onChange={handleFileChange}
                className="w-full"
              />
              <p className="text-sm text-gray-500">
                Tamanho máximo: {MAX_FILE_SIZE / 1024 / 1024}MB
              </p>
            </div>
            <Button type="submit" disabled={loading || !file}>
              {loading ? 'Processando...' : 'Processar Arquivo'}
            </Button>
          </form>

          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {resultado && (
            <div className="mt-4">
              <h3 className="font-bold mb-2">Resultado do Processamento</h3>
              <Button
                onClick={handleDownload}
                className="mt-2"
              >
                Baixar Resultados
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 