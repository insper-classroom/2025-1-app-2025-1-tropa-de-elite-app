'use client'
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from 'next/link';
import { useAppState } from '@/lib/app-context';
import { useEffect, useState } from 'react';

export default function Home() {
  const { 
    files, 
    uploadSuccess, 
    processedData, 
    loading, 
    processing, 
    error,
    setFiles: setFile, 
    uploadFiles, 
    processData, 
    resetError,
    resetState
  } = useAppState();
  
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Verificar conexão com o backend
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/status');
        if (response.ok) {
          setBackendStatus('online');
        } else {
          setBackendStatus('offline');
        }
      } catch (error) {
        console.error('Erro ao verificar backend:', error);
        setBackendStatus('offline');
      }
    };
    
    checkBackendStatus();
  }, []);

  const handleFileChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(field, e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    await uploadFiles();
  };

  const handleProcessData = async () => {
    await processData();
  };

  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Sistema de Detecção de Fraudes</h1>

      {backendStatus === 'offline' && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>
            <div className="flex flex-col gap-1">
              <span className="font-semibold">O servidor backend não está acessível.</span>
              <span className="text-sm">
                Verifique se o servidor está em execução em http://localhost:8000 ou se há problemas de rede.
                As funcionalidades de análise e upload de arquivos não funcionarão até que o servidor esteja online.
              </span>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-2 self-start"
                onClick={() => {
                  setBackendStatus('checking');
                  fetch('http://localhost:8000/api/status')
                    .then(res => {
                      if (res.ok) setBackendStatus('online');
                      else setBackendStatus('offline');
                    })
                    .catch(() => setBackendStatus('offline'));
                }}
              >
                Tentar reconectar
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}
      
      {backendStatus === 'checking' && (
        <Alert className="mb-6">
          <AlertDescription>
            Verificando conexão com o servidor de backend...
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Upload de Arquivos</CardTitle>
            <CardDescription>
              Faça o upload dos arquivos feather necessários para análise
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid gap-2">
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
              
              {processedData && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    if (window.confirm('Isso irá limpar todos os dados carregados e resultados. Deseja continuar?')) {
                      resetState();
                    }
                  }}
                >
                  Limpar Dados e Reiniciar
                </Button>
              )}
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
                  Ir para Operações
                </Button>
              </Link>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
