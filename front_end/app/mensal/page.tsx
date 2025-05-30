import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

export default function MensalPage() {
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Análise Mensal</h1>
      
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
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um mês" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="june">Junho 2024</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="model">Selecione o Modelo</Label>
                <Select>
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

              <Button className="w-full">Iniciar Análise</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resultados da Análise</CardTitle>
            <CardDescription>
              Resultados da detecção de fraudes do mês
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total de Transações</p>
                      <p className="text-2xl font-bold">0</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Transações Suspeitas</p>
                      <p className="text-2xl font-bold">0</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Taxa de Fraude</p>
                      <p className="text-2xl font-bold">0%</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <p className="text-center text-muted-foreground">
                  Os resultados detalhados aparecerão aqui
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
} 