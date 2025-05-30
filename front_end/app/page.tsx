'use client'
import { useState } from 'react'
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import Link from 'next/link';

export default function Home() {
  const [files, setFiles] = useState({
    transacoes: null as File | null,
    usuarios: null as File | null,
    produtos: null as File | null
  });
  const [modelo, setModelo] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (field: keyof typeof files) => (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFiles(prev => ({
        ...prev,
        [field]: e.target.files![0]
      }));
    }
  };

  const handleSubmit = async () => {
    if (!files.transacoes || !files.usuarios || !files.produtos || !modelo) {
      setError('Por favor, selecione todos os arquivos e o modelo');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('transacoes', files.transacoes);
      formData.append('usuarios', files.usuarios);
      formData.append('produtos', files.produtos);
      formData.append('modelo', modelo);

      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Erro ao fazer upload dos arquivos');
      }

      setSuccess(true);
      setFiles({
        transacoes: null,
        usuarios: null,
        produtos: null
      });
      setModelo('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar o upload');
    } finally {
      setLoading(false);
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
              Faça o upload dos arquivos necessários para análise
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="file1">Arquivo de Transações</Label>
                <Input 
                  id="file1" 
                  type="file" 
                  accept=".csv,.xlsx" 
                  onChange={handleFileChange('transacoes')}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="file2">Arquivo de Usuários</Label>
                <Input 
                  id="file2" 
                  type="file" 
                  accept=".csv,.xlsx" 
                  onChange={handleFileChange('usuarios')}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="file3">Arquivo de Produtos</Label>
                <Input 
                  id="file3" 
                  type="file" 
                  accept=".csv,.xlsx" 
                  onChange={handleFileChange('produtos')}
                />
              </div>
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

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert>
                  <AlertDescription>Arquivos enviados com sucesso!</AlertDescription>
                </Alert>
              )}

              <Button 
                className="w-full" 
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? 'Enviando...' : 'Fazer Upload'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/transacao">
            <Card className="cursor-pointer hover:bg-accent/50 transition-colors">
              <CardHeader>
                <CardTitle>Análise de Transação Única</CardTitle>
                <CardDescription>
                  Analise uma transação específica para detecção de fraude
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Link href="/mensal">
            <Card className="cursor-pointer hover:bg-accent/50 transition-colors">
              <CardHeader>
                <CardTitle>Análise Mensal</CardTitle>
                <CardDescription>
                  Analise todas as transações de um mês específico
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>
      </div>
    </main>
  );
}
