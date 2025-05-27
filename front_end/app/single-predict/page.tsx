"use client";

import { useState } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { TransactionSearch } from "@/components/single-predict/transaction-search";
import { TransactionDetails } from "@/components/single-predict/transaction-details";
import { PredictionResultCard } from "@/components/single-predict/prediction-result";
import { api } from "@/lib/api";
import { PredictionResult, Transaction } from "@/types";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function SinglePredictPage() {
  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const handleSearch = async (transactionId: string) => {
    if (!transactionId.trim()) return;

    setLoading(true);
    setPredictionResult(null);
    
    try {
      const data = await api.getTransaction(transactionId);
      setTransaction(data);
    } catch (error) {
      console.error("Error fetching transaction:", error);
      toast.error("Failed to fetch transaction details");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!transaction) return;
    
    setAnalyzing(true);
    
    try {
      const result = await api.predictTransaction(transaction.id);
      setPredictionResult(result);
      toast.success("Transaction analysis complete");
    } catch (error) {
      console.error("Error analyzing transaction:", error);
      toast.error("Failed to analyze transaction");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="container py-6">
      <PageHeader
        title="Single Transaction Analysis"
        description="Analyze individual transactions for potential fraud"
      />

      <div className="mt-6">
        <TransactionSearch onSearch={handleSearch} />
      </div>

      {loading && (
        <div className="flex justify-center my-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {transaction && !loading && (
        <div className="mt-8 space-y-8">
          <TransactionDetails transaction={transaction} />
          
          {!predictionResult && (
            <div className="flex justify-center">
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
              >
                {analyzing && <Loader2 className="h-4 w-4 animate-spin" />}
                {analyzing ? "Analyzing..." : "Analyze Transaction"}
              </button>
            </div>
          )}

          {predictionResult && (
            <PredictionResultCard result={predictionResult} />
          )}
        </div>
      )}
    </div>
  );
}