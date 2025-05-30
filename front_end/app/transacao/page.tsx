'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

export default function TransacaoPage() {
  const [transacao, setTransacao] = useState('');
  const [modelo, setModelo] = useState('');
  const [resultado, setResultado] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!transacao || !modelo) {
      setError('Por favor, preencha todos os campos');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/api/analise/transacao', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          modelo,
          transacao: JSON.parse(transacao)
        }),
      });

      if (!response.ok) {
        throw new Error('Erro ao analisar transação');
      }

      const data = await response.json();
      setResultado(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar a transação');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Análise de Transação Única</h1>
      
      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Detecção de Fraude</CardTitle>
            <CardDescription>
              Insira os dados da transação para análise
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="model">Selecione o Modelo</Label>
                <Select value={modelo} onValueChange={setModelo}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um modelo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="model1">Modelo 1</SelectItem>
                    <SelectItem value="model2">Modelo 2</SelectItem>
                    <SelectItem value="model3">Modelo 3</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="grid gap-2">
                <Label htmlFor="transaction">Dados da Transação</Label>
                <Textarea 
                  id="transaction" 
                  value={transacao}
                  onChange={(e) => setTransacao(e.target.value)}
                  placeholder="Cole aqui os dados da transação em formato JSON"
                  className="h-32 font-mono"
                />
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button 
                className="w-full" 
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? 'Analisando...' : 'Analisar Transação'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {resultado && (
          <Card>
            <CardHeader>
              <CardTitle>Resultado da Análise</CardTitle>
              <CardDescription>
                Resultado da detecção de fraude
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted rounded-lg">
                <pre className="whitespace-pre-wrap font-mono">
                  {JSON.stringify(resultado, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
} 