'use client'
import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { api } from '@/lib/api-clean';
import { useAppState } from '@/lib/app-context';
import { ModelInfo, PredictionResult, BatchPredictionResult, SearchResult } from '@/types';
import { useRouter } from 'next/navigation';

export default function OperacoesPage() {
  // Usar o contexto global da aplicação
  const { 
    selectedModel, 
    models, 
    error: globalError, 
    setSelectedModel 
  } = useAppState();
  
  const router = useRouter();
  
  // Estados locais para a página
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [searching, setSearching] = useState(false);
  const [selectedRowIndex, setSelectedRowIndex] = useState<number | null>(null);
  
  // Predictions
  const [predictingSingle, setPredictingSingle] = useState(false);
  const [predictingAll, setPredictingAll] = useState(false);
  const [singlePrediction, setSinglePrediction] = useState<PredictionResult | null>(null);
  const [allPredictions, setAllPredictions] = useState<BatchPredictionResult | null>(null);
  
  // Date range filter
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
    // Não precisamos buscar modelos aqui, pois já estão disponíveis no contexto global
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
      setError(err instanceof Error ? err.message : 'Erro ao buscar dados. Verifique a conexão com o backend.');
      // Se houve erro de conexão, atualizar o status do backend
      if (err instanceof Error && err.message.includes('conexão')) {
        setBackendStatus('offline');
      }
    } finally {
      setSearching(false);
    }
  };
    const handleSinglePredict = async () => {
    if (!selectedModel || selectedRowIndex === null) {
      setError('Selecione um modelo e uma linha para analisar');
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
      console.error('Erro na predição única:', err);
      setError(err instanceof Error ? err.message : 'Erro ao fazer previsão. Verifique a conexão com o backend.');
      // Se houve erro de conexão, atualizar o status do backend
      if (err instanceof Error && err.message.includes('conexão')) {
        setBackendStatus('offline');
      }
    } finally {
      setPredictingSingle(false);
    }
  };
    const handleAllPredict = async () => {
    if (!selectedModel) {
      setError('Selecione um modelo para analisar todo o dataset');
      return;
    }
    
    try {
      setPredictingAll(true);
      setError(null);
      
      // Verificar conexão com o backend antes de fazer a predição
      if (backendStatus === 'offline') {
        throw new Error('O servidor backend não está acessível. Verifique a conexão e tente novamente.');
      }
      
      const result = await api.predictAll(
        selectedModel.nome,
        selectedModel.variante,
        selectedModel.versao
      );
      setAllPredictions(result);
    } catch (err) {
      console.error('Erro na predição em lote:', err);
      setError(err instanceof Error ? err.message : 'Erro ao fazer previsão para todo o dataset. Verifique a conexão com o backend.');
      // Se houve erro de conexão, atualizar o status do backend
      if (err instanceof Error && err.message.includes('conexão')) {
        setBackendStatus('offline');
      }
    } finally {
      setPredictingAll(false);
    }
  };
  
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Operações do Sistema</h1>
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Selecione o Modelo</CardTitle>
          <CardDescription>
            Escolha o modelo que deseja utilizar para fazer previsões
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select 
            onValueChange={(value) => {
              const model = models.find(m => `${m.nome}_${m.variante}_${m.versao}` === value);
              setSelectedModel(model || null);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione um modelo" />
            </SelectTrigger>
            <SelectContent>
              {models.map((model) => (
                <SelectItem 
                  key={`${model.nome}_${model.variante}_${model.versao}`} 
                  value={`${model.nome}_${model.variante}_${model.versao}`}
                >
                  {model.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>
      
      {globalError && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}
      
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
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
                className="mt-2 self-start"                onClick={() => {
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
      
      {backendStatus === 'online' && (
        <Tabs defaultValue="single" className="mb-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="single">Análise Única</TabsTrigger>
            <TabsTrigger value="all">Análise Mensal</TabsTrigger>
          </TabsList>
          
          <TabsContent value="single">
            <Card>
              <CardHeader>
                <CardTitle>Análise Única</CardTitle>              <CardDescription>
                  Busque uma transação específica por card_bin ou filtre por período
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">              <div className="space-y-4">
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
                </div>
                  
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
                    <Button 
                      className="w-full"
                      onClick={handleSinglePredict}
                      disabled={predictingSingle || !selectedModel}
                    >
                      {predictingSingle ? 'Analisando...' : 'Rodar Previsão Única'}
                    </Button>
                  )}
                  
                  {singlePrediction && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Resultado da Previsão</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="font-medium">Previsão:</span>
                            <span className={singlePrediction.prediction === 1 ? "text-red-500 font-bold" : "text-green-500 font-bold"}>
                              {singlePrediction.prediction === 1 ? 'FRAUDE' : 'NÃO FRAUDE'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="font-medium">Probabilidade:</span>
                            <span>{(singlePrediction.probability * 100).toFixed(2)}%</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="all">
            <Card>
              <CardHeader>
                <CardTitle>Análise Mensal</CardTitle>
                <CardDescription>
                  Analise todos os dados processados
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Button 
                    className="w-full"
                    onClick={handleAllPredict}
                    disabled={predictingAll || !selectedModel}
                  >
                    {predictingAll ? 'Analisando...' : 'Rodar Previsão em Todo o Dataset'}
                  </Button>
                  
                  {allPredictions && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Resultado da Análise</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <Card>
                              <CardHeader className="py-4">
                                <CardTitle className="text-center">Total de Transações</CardTitle>
                              </CardHeader>
                              <CardContent className="text-3xl text-center pb-4">
                                {allPredictions.predictions.length}
                              </CardContent>
                            </Card>
                            <Card>
                              <CardHeader className="py-4">
                                <CardTitle className="text-center">Fraudes Detectadas</CardTitle>
                              </CardHeader>
                              <CardContent className="text-3xl text-center text-red-500 pb-4">
                                {allPredictions.predictions.filter(p => p === 1).length}
                              </CardContent>
                            </Card>
                          </div>
                          
                          <div className="flex justify-between bg-muted p-4 rounded-md">
                            <span className="font-medium">Taxa de Fraude:</span>
                            <span className="font-bold">
                              {((allPredictions.predictions.filter(p => p === 1).length / allPredictions.predictions.length) * 100).toFixed(2)}%
                            </span>
                          </div>
                          
                          <div className="flex justify-between bg-muted p-4 rounded-md">
                            <span className="font-medium">Threshold utilizado:</span>
                            <span>{allPredictions.threshold}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </main>
  );
}
