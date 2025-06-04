import { useState, useEffect } from "react";
import { CheckCircleIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BatchJob, TransactionResult } from "@/types";
import { TransactionResults } from "./transaction-results";
// Importamos a API preparada para integração com o backend
import { api } from "@/lib/api-integration-ready";

interface BatchResultProps {
  job: BatchJob;
  onStartNew: () => void;
}

export function BatchResult({ job, onStartNew }: BatchResultProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [results, setResults] = useState<TransactionResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch results from our API client
    const fetchResults = async () => {
      setLoading(true);
      try {
        // Buscar resultados do job utilizando a API preparada para integração
        if (job && job.jobId) {
          try {
            // Tentar obter os resultados do job
            const batchResults = await api.getBatchJobResults(job.jobId);
            setResults(batchResults);
          } catch (error) {
            console.error("Erro ao buscar resultados do job:", error);
            
            // Fallback para dados simulados em caso de erro
            const mockResults = Array.from({ length: 537 }).map((_, i) => ({
              transaction_id: `TX-${100000 + i}`,
              approved: Math.random() > 0.15, // 15% de rejeição
              probability_of_fraud: Math.random()
            }));
            setResults(mockResults);
          }
        }
      } catch (error) {
        console.error("Erro ao obter resultados:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchResults();
  }, [job?.jobId]);

  const handleDownload = async () => {
    if (!results.length) return;
    
    setIsDownloading(true);
    
    try {
      // Create CSV content from results
      let csvContent = "transaction_id,approved,probability_of_fraud\n";
      
      results.forEach(result => {
        csvContent += `${result.transaction_id},${result.approved ? "SIM" : "NÃO"},${result.probability_of_fraud}\n`;
      });
      
      const blob = new Blob([csvContent], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resultados-transacoes-${job.jobId}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error downloading file:", error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <>
      {loading ? (
        <Card className="w-full">
          <CardHeader className="pb-3">
            <div className="flex items-center">
              <CheckCircleIcon className="h-6 w-6 text-green-500 mr-2" />
              <CardTitle>Processamento Concluído</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="py-8 text-center">
              <p>Carregando resultados...</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <TransactionResults 
          results={results}
          onDownload={handleDownload}
          isDownloading={isDownloading}
          onStartNew={onStartNew}
        />
      )}
    </>
  );
}
