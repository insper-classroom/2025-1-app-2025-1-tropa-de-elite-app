"use client";

import { useState, useEffect } from "react";
import { CheckCircleIcon, XCircleIcon, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface TransactionResult {
  transaction_id: string;
  approved: boolean;
  probability_of_fraud: number;
}

interface TransactionResultsProps {
  results: TransactionResult[];
  onDownload: () => void;
  isDownloading: boolean;
  onStartNew: () => void;
}

export function TransactionResults({ 
  results, 
  onDownload, 
  isDownloading,
  onStartNew
}: TransactionResultsProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredResults, setFilteredResults] = useState<TransactionResult[]>(results);
  const resultsPerPage = 100;

  useEffect(() => {
    if (searchTerm) {
      setFilteredResults(
        results.filter(result => 
          result.transaction_id.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
      setCurrentPage(1);
    } else {
      setFilteredResults(results);
    }
  }, [searchTerm, results]);

  const totalPages = Math.max(1, Math.ceil(filteredResults.length / resultsPerPage));
  const displayedResults = filteredResults.slice(
    (currentPage - 1) * resultsPerPage, 
    currentPage * resultsPerPage
  );

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center">
          <CheckCircleIcon className="h-6 w-6 text-green-500 mr-2" />
          <CardTitle>Análise de Transações Concluída</CardTitle>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex justify-between items-center">
          <div className="text-sm text-muted-foreground">
            {filteredResults.length} transações processadas
          </div>
          
          <div className="max-w-sm">
            <Label htmlFor="search" className="sr-only">Buscar transação</Label>
            <Input
              id="search"
              placeholder="Buscar ID da transação..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
        </div>
        
        <div className="border rounded-md overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left font-medium">ID da Transação</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Probabilidade de Fraude</th>
              </tr>
            </thead>
            <tbody>
              {displayedResults.length > 0 ? (
                displayedResults.map((result) => (
                  <tr key={result.transaction_id} className="border-t">
                    <td className="px-4 py-3">{result.transaction_id}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        result.approved
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}>
                        {result.approved ? (
                          <>
                            <CheckCircleIcon className="h-3 w-3 mr-1" />
                            Aprovado
                          </>
                        ) : (
                          <>
                            <XCircleIcon className="h-3 w-3 mr-1" />
                            Rejeitado
                          </>
                        )}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                          <div 
                            className={`h-2.5 rounded-full ${
                              result.probability_of_fraud < 0.3 
                                ? "bg-green-500" 
                                : result.probability_of_fraud < 0.7 
                                  ? "bg-yellow-500" 
                                  : "bg-red-500"
                            }`} 
                            style={{ width: `${result.probability_of_fraud * 100}%` }}
                          ></div>
                        </div>
                        <span>{(result.probability_of_fraud * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">
                    {searchTerm ? "Nenhuma transação encontrada com este ID" : "Nenhuma transação disponível"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {filteredResults.length > resultsPerPage && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Mostrando {((currentPage - 1) * resultsPerPage) + 1} a {Math.min(currentPage * resultsPerPage, filteredResults.length)} de {filteredResults.length} resultados
            </p>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm">
                {currentPage} de {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex flex-col sm:flex-row gap-3 pt-6">
        <Button
          className="w-full sm:w-auto"
          onClick={onDownload}
          disabled={isDownloading || filteredResults.length === 0}
        >
          <Download className="mr-2 h-4 w-4" />
          {isDownloading ? "Baixando..." : "Baixar Resultados"}
        </Button>
        <Button 
          variant="outline" 
          className="w-full sm:w-auto"
          onClick={onStartNew}
        >
          Processar Novas Transações
        </Button>
      </CardFooter>
    </Card>
  );
}
