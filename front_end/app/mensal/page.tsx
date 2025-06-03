'use client'

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRouter } from 'next/navigation';
import { useAppState } from '@/lib/app-context';
import { api } from '@/lib/api-clean';
import { BatchPredictionResult } from '@/types';
import { Progress } from "@/components/ui/progress";

export default function MensalPage() {
  const router = useRouter();
  const { selectedModel, processedData, models, error: globalError } = useAppState();
  
  const [error, setError] = useState<string | null>(null);
  const [predictingAll, setPredictingAll] = useState(false);
  const [allPredictions, setAllPredictions] = useState<BatchPredictionResult | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<string>("june");
  const [analysisComplete, setAnalysisComplete] = useState(false);
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

  // Verificar se temos os dados necessários para esta página
  if (!processedData) {
    return (
      <div className="container mx-auto p-4 text-center">
        <Alert variant="warning">
          <AlertDescription>
            Por favor, faça o upload e processamento dos dados antes de analisar mensalmente.
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
  }  const handleRunAnalysis = async () => {
    if (!selectedModel) {
      setError('Por favor, selecione um modelo para análise');
      return;
    }
    
    try {
      setPredictingAll(true);
      setError(null);
      
      // Verificar conexão com o backend antes de fazer a predição
      if (backendStatus === 'offline') {
        throw new Error('O servidor backend não está acessível. Verifique a conexão e tente novamente.');
      }
      
      // Chamar API para predições em lote
      const results = await api.predictAll(
        selectedModel.nome,
        selectedModel.variante,
        selectedModel.versao
      );
      
      setAllPredictions(results);
      setAnalysisComplete(true);
    } catch (err) {
      console.error('Erro na análise mensal:', err);
      setError(err instanceof Error ? err.message : 'Erro ao processar análise mensal. Verifique se o backend está em execução.');
      // Se houve erro de conexão, atualizar o status do backend
      if (err instanceof Error && err.message.includes('conexão')) {
        setBackendStatus('offline');
      }
      setAnalysisComplete(false);
    } finally {
      setPredictingAll(false);
    }
  };

  // Calcular estatísticas de fraude se tivermos predições
  const fraudStats = allPredictions ? {
    total: allPredictions.predictions.length,    fraudCount: allPredictions.predictions.filter((p: number) => p === 1).length,
    fraudRate: (allPredictions.predictions.filter((p: number) => p === 1).length / allPredictions.predictions.length) * 100
  } : null;

  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Análise Mensal</h1>
      
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
      
      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Configuração da Análise</CardTitle>
            <CardDescription>
              Selecione o mês e o modelo para análise
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="month">Selecione o Mês</Label>
                <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um mês" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="june">Junho 2024</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="model">Modelo Selecionado</Label>
                <div className="p-2 border rounded-md bg-muted">
                  {selectedModel.label}
                </div>
              </div>              <Button 
                className="w-full" 
                onClick={handleRunAnalysis}
                disabled={predictingAll || backendStatus !== 'online'}
              >
                {predictingAll ? 'Processando...' : 'Iniciar Análise'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resultados da Análise</CardTitle>
            <CardDescription>
              Resultados da detecção de fraudes do mês
            </CardDescription>
          </CardHeader>          <CardContent>            {predictingAll ? (
              <div className="space-y-4">
                <p className="text-center text-muted-foreground">Processando dados...</p>
                <Progress value={45} className="w-full animate-pulse" />
                <div className="bg-muted p-3 rounded-md border border-border">
                  <p className="text-xs text-muted-foreground mb-2">Log de processamento:</p>
                  <div className="text-xs font-mono bg-background p-2 rounded overflow-y-auto h-24">
                    <p>Iniciando análise de fraude...</p>
                    <p>Carregando modelo {selectedModel.nome} - {selectedModel.variante} v{selectedModel.versao}</p>
                    <p>Processando {selectedMonth === 'june' ? 'Junho/2024' : selectedMonth}</p>
                    <p className="text-green-500 animate-pulse">Analisando transações...</p>
                  </div>
                </div>
                <p className="text-center text-xs text-muted-foreground">
                  Aguarde enquanto o modelo analisa todas as transações.
                  Este processo pode levar alguns segundos.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">Total de Transações</p>
                        <p className="text-2xl font-bold">{fraudStats?.total || 0}</p>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">Transações Suspeitas</p>
                        <p className="text-2xl font-bold text-red-500">{fraudStats?.fraudCount || 0}</p>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">Taxa de Fraude</p>
                        <p className="text-2xl font-bold">{fraudStats ? `${fraudStats.fraudRate.toFixed(2)}%` : '0%'}</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>                {allPredictions && analysisComplete ? (
                  <div className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle>Distribuição de Probabilidades</CardTitle>
                        <CardDescription>
                          Visão geral das probabilidades de fraude nas transações
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="h-60 bg-muted rounded-lg flex items-center justify-center">
                          <div className="text-center space-y-2">
                            <p className="text-muted-foreground font-medium">Gráfico de distribuição de probabilidades de fraude</p>
                            <p className="text-xs text-muted-foreground">
                              {fraudStats?.fraudCount} transações acima do threshold de {allPredictions.threshold * 100}%
                            </p>
                          </div>
                        </div>
                        <div className="mt-4 space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="font-medium">Threshold de detecção:</span>
                            <span>{(allPredictions.threshold * 100).toFixed(2)}%</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="font-medium">Média de probabilidade:</span>
                            <span>
                              {(allPredictions.probabilities.reduce((a, b) => a + b, 0) / 
                                allPredictions.probabilities.length * 100).toFixed(2)}%
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ) : (                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-center text-muted-foreground">
                      {analysisComplete ? 'Nenhum resultado disponível' : 'Execute a análise para ver os resultados detalhados'}
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
        
        {analysisComplete && allPredictions && (
          <Card>
            <CardHeader>
              <CardTitle>Ações Recomendadas</CardTitle>
              <CardDescription>
                Com base na análise de fraude, recomendamos as seguintes ações
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-md bg-amber-50">
                  <h3 className="font-medium mb-2">Alta Prioridade</h3>
                  <p className="text-sm text-muted-foreground">
                    Investigar as {fraudStats?.fraudCount} transações identificadas como potenciais fraudes.
                  </p>
                </div>
                
                <div className="p-4 border rounded-md">
                  <h3 className="font-medium mb-2">Melhoria do Sistema</h3>
                  <p className="text-sm text-muted-foreground">
                    A taxa de detecção de fraude atual é de {fraudStats?.fraudRate.toFixed(2)}%. 
                    Considere ajustar o threshold ou realizar mais treinamento para melhorar a precisão.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}