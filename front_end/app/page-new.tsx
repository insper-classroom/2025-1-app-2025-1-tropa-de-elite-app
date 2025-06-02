'use client'
import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from 'next/link';
import { api } from '@/lib/api-new';
import { ProcessedData } from '@/types';

export default function Home() {  const [files, setFiles] = useState({
    payers: null as File | null,
    seller_terminals: null as File | null,
    transactional_train: null as File | null
  });
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null);

  const handleFileChange = (field: keyof typeof files) => (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFiles(prev => ({
        ...prev,
        [field]: e.target.files[0]
      }));
    }
  };

  const handleUpload = async () => {
    if (!files.payers || !files.seller_terminals || !files.transactional_train) {
      setError('Por favor, selecione todos os arquivos feather');
      return;
    }

    try {
      setLoading(true);
      setError(null);      await api.uploadFiles(
        files.payers,
        files.seller_terminals,
        files.transactional_train
      );

      setUploadSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar o upload');
      setUploadSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessData = async () => {
    try {
      setProcessing(true);
      setError(null);

      const data = await api.processData();
      setProcessedData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar os dados');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Sistema de Detecção de Fraudes</h1>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Upload de Arquivos</CardTitle>
            <CardDescription>
              Faça o upload dos arquivos feather necessários para análise
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">              <div className="grid gap-2">
                <Label htmlFor="payers">Arquivo de Payers (payers.feather)</Label>
                <Input
                  id="payers"
                  type="file"
                  accept=".feather"
                  onChange={handleFileChange('payers')}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="seller_terminals">Arquivo de Seller Terminals (seller_terminals.feather)</Label>
                <Input
                  id="seller_terminals"
                  type="file"
                  accept=".feather"
                  onChange={handleFileChange('seller_terminals')}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="transactional_train">Arquivo de Transações (transactional_train.feather)</Label>
                <Input
                  id="transactional_train"
                  type="file"
                  accept=".feather"
                  onChange={handleFileChange('transactional_train')}
                />
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {uploadSuccess && (
                <Alert>
                  <AlertDescription>Arquivos enviados com sucesso!</AlertDescription>
                </Alert>
              )}

              <Button
                className="w-full"
                onClick={handleUpload}
                disabled={loading}
              >
                {loading ? 'Enviando...' : 'Fazer Upload'}
              </Button>

              <Button
                className="w-full"
                onClick={handleProcessData}
                disabled={processing || !uploadSuccess}
              >
                {processing ? 'Processando...' : 'Gerar Features'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {processedData && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Dados Processados</CardTitle>
                <CardDescription>
                  Primeiras 5 linhas dos dados processados
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {processedData.head.length > 0 && 
                          Object.keys(processedData.head[0]).map(column => (
                            <TableHead key={column}>{column}</TableHead>
                          ))
                        }
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {processedData.head.map((row, i) => (
                        <TableRow key={i}>
                          {Object.values(row).map((value, j) => (
                            <TableCell key={j}>
                              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Features Extraídas</CardTitle>
                <CardDescription>
                  Lista de colunas/features extraídas
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {processedData.features.map(feature => (
                    <div key={feature} className="p-2 bg-muted rounded-md">
                      {feature}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-center mt-4">
              <Link href="/modelos">
                <Button size="lg">
                  Ir para Modelos
                </Button>
              </Link>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
