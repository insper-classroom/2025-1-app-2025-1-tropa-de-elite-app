'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { Progress } from "@/components/ui/progress";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { useAppState } from '@/lib/app-context';
import { api } from '@/lib/api-clean';
import { PredictionResult, SearchResult } from '@/types';
import { useRouter } from 'next/navigation';

export default function TransacaoPage() {
  const router = useRouter();
  const { selectedModel, processedData, error: globalError } = useAppState();
  
  // Verificação de status do backend
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [searching, setSearching] = useState(false);
  const [selectedRowIndex, setSelectedRowIndex] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Prediction
  const [predictingSingle, setPredictingSingle] = useState(false);
  const [singlePrediction, setSinglePrediction] = useState<PredictionResult | null>(null);
  
  // Date range filter
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
  
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

  // Verificar se temos os dados necessários para esta página
  if (!processedData) {
    return (
      <div className="container mx-auto p-4 text-center">
        <Alert variant="warning">
          <AlertDescription>
            Por favor, faça o upload e processamento dos dados antes de analisar transações.
          </AlertDescription>
        </Alert>
        <Button className="mt-4" onClick={() => router.push('/')}>
          Ir para Upload
        </Button>
      </div>
    );
  }

  if (!selectedModel) {
    return (
      <div className="container mx-auto p-4 text-center">
        <Alert variant="warning">
          <AlertDescription>
            Por favor, selecione um modelo antes de analisar transações.
          </AlertDescription>
        </Alert>
        <Button className="mt-4" onClick={() => router.push('/modelos')}>
          Selecionar Modelo
        </Button>
      </div>
    );
  }

  const handleSearch = async () => {
    if (!searchQuery.trim() && (!dateRange || !dateRange.from)) {
      setError('Por favor, digite um termo de busca ou selecione um período de datas');
      return;
    }
    
    try {
      setSearching(true);
      setError(null);
      
      // Verificar conexão com o backend antes de fazer a busca
      if (backendStatus === 'offline') {
        throw new Error('O servidor backend não está acessível. Verifique a conexão e tente novamente.');
      }
      
      // Construir a query de busca
      let query = searchQuery.trim();
      
      // Adicionar filtro de data se estiver definido
      if (dateRange && dateRange.from) {
        const fromDate = format(dateRange.from, 'yyyy-MM-dd');
        const toDate = dateRange.to ? format(dateRange.to, 'yyyy-MM-dd') : fromDate;
        query = `${query} ${fromDate} ${toDate}`.trim();
      }
      
      const results = await api.searchRows(query);
      setSearchResults(results);
      setSelectedRowIndex(null);
      setSinglePrediction(null);
    } catch (err) {
      console.error('Erro na busca:', err);
      setError(err instanceof Error ? err.message : 'Erro ao buscar dados. Verifique se o backend está em execução.');
      // Se houve erro de conexão, atualizar o status do backend
      if (err instanceof Error && err.message.includes('conexão')) {
        setBackendStatus('offline');
      }
    } finally {
      setSearching(false);
    }
  };

  const handleSinglePredict = async () => {
    if (selectedRowIndex === null) {
      setError('Selecione uma linha para analisar');
      return;
    }
    
    try {
      setPredictingSingle(true);
      setError(null);
      
      // Verificar conexão com o backend antes de fazer a predição
      if (backendStatus === 'offline') {
        throw new Error('O servidor backend não está acessível. Verifique a conexão e tente novamente.');
      }
      
      const result = await api.predictRow(
        selectedModel.nome,
        selectedModel.variante,
        selectedModel.versao,
        selectedRowIndex
      );
      setSinglePrediction(result);
    } catch (err) {
      console.error('Erro na previsão:', err);
      setError(err instanceof Error ? err.message : 'Erro ao fazer previsão. Verifique se o backend está em execução.');
      // Se houve erro de conexão, atualizar o status do backend
      if (err instanceof Error && err.message.includes('conexão')) {
        setBackendStatus('offline');
      }
    } finally {
      setPredictingSingle(false);
    }
  };

  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Análise de Transação Única</h1>
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Modelo Selecionado</CardTitle>
          <CardDescription>
            {`${selectedModel.nome} - ${selectedModel.variante} - ${selectedModel.versao}`}
          </CardDescription>
        </CardHeader>
      </Card>
      
      {(error || globalError) && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error || globalError}</AlertDescription>
        </Alert>
      )}
      
      {backendStatus === 'checking' && (
        <Alert variant="warning" className="mb-6">
          <AlertDescription>Verificando conexão com o backend...</AlertDescription>
        </Alert>
      )}
      
      {backendStatus === 'offline' && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>
            <div className="flex flex-col gap-1">
              <span className="font-semibold">O servidor backend não está acessível.</span>
              <span className="text-sm">
                Verifique se o servidor está em execução em http://localhost:8000 ou se há problemas de rede.
                As funcionalidades de análise não funcionarão até que o servidor esteja online.
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
      
      <Card>
        <CardHeader>
          <CardTitle>Busque uma Transação</CardTitle>
          <CardDescription>
            Busque uma transação específica por card_bin ou filtre por período
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Buscar por card_bin"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Filtrar por Período de Data</Label>
              <DateRangePicker 
                dateRange={dateRange}
                onDateRangeChange={setDateRange}
              />
            </div>
            
            <Button 
              className="w-full" 
              onClick={handleSearch} 
              disabled={searching}
            >
              {searching ? 'Buscando...' : 'Buscar'}
            </Button>
            
            {searchResults && searchResults.rows.length > 0 ? (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Selecionar</TableHead>
                      {searchResults.columns.slice(0, 5).map(column => (
                        <TableHead key={column}>{column}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {searchResults.rows.map((row, index) => (
                      <TableRow 
                        key={index}
                        className={selectedRowIndex === index ? "bg-accent" : ""}
                      >
                        <TableCell>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setSelectedRowIndex(index)}
                          >
                            Selecionar
                          </Button>
                        </TableCell>
                        {Object.values(row).slice(0, 5).map((value, i) => (
                          <TableCell key={i}>
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : searchResults ? (
              <Alert>
                <AlertDescription>Nenhum resultado encontrado</AlertDescription>
              </Alert>
            ) : null}
            
            {selectedRowIndex !== null && (
              <div className="space-y-4">
                <Button 
                  className="w-full"
                  onClick={handleSinglePredict}
                  disabled={predictingSingle}
                >
                  {predictingSingle ? 'Analisando...' : 'Rodar Previsão'}
                </Button>
                
                {predictingSingle && (
                  <div className="space-y-2">
                    <Progress value={65} className="w-full animate-pulse" />
                    <div className="bg-muted p-3 rounded-md border border-border">
                      <p className="text-xs text-muted-foreground mb-2">Log de processamento:</p>
                      <div className="text-xs font-mono bg-background p-2 rounded overflow-y-auto h-16">
                        <p>Iniciando análise de fraude...</p>
                        <p>Carregando modelo {selectedModel.nome} - {selectedModel.variante} v{selectedModel.versao}</p>
                        <p className="text-green-500 animate-pulse">Analisando transação #{selectedRowIndex}...</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {singlePrediction && (
              <Card>
                <CardHeader>
                  <CardTitle>Resultado da Previsão</CardTitle>
                  <CardDescription>
                    Análise de detecção de fraude para a transação selecionada
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div 
                      className={`p-4 rounded-md border-2 border-l-8 mb-4 transition-colors ${
                        singlePrediction.prediction === 1 
                          ? "bg-red-50 border-red-200 border-l-red-500" 
                          : "bg-green-50 border-green-200 border-l-green-500"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Resultado da análise:</span>
                        <span className={singlePrediction.prediction === 1 ? "text-red-600 font-bold" : "text-green-600 font-bold"}>
                          {singlePrediction.prediction === 1 ? 'FRAUDE DETECTADA' : 'TRANSAÇÃO NORMAL'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="font-medium">Probabilidade de fraude:</span>
                        <span>{(singlePrediction.probability * 100).toFixed(2)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Índice na base de dados:</span>
                        <span>{singlePrediction.row_index}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Threshold de detecção:</span>
                        <span>50%</span>
                      </div>
                    </div>
                    
                    {singlePrediction.prediction === 1 && (
                      <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-md">
                        <p className="text-sm font-medium text-amber-800">Recomendação:</p>
                        <p className="text-xs text-amber-700 mt-1">
                          Esta transação foi classificada como suspeita. Recomenda-se uma revisão manual
                          ou contato com o titular do cartão para validação.
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>
    </main>
  );
}