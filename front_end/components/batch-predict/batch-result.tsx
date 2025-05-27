"use client";

import { useState } from "react";
import { CheckCircleIcon, Download, FileTextIcon, ExternalLinkIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { BatchJob } from "@/types";
import Link from "next/link";

interface BatchResultProps {
  job: BatchJob;
  onStartNew: () => void;
}

export function BatchResult({ job, onStartNew }: BatchResultProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    if (!job.downloadUrl) return;
    
    setIsDownloading(true);
    
    try {
      // In a real application, this would download the actual file
      // For demo purposes, we'll create a simple CSV and download it
      const csvContent = "transaction_id,amount,merchant_id,customer_id,decision,score,version,timestamp\n" +
        "TX-12345,299.99,MERCH-123,CUST-456,NOT_FRAUD,0.12,v1.2.3,2023-05-15T10:30:45Z\n" +
        "TX-67890,1299.99,MERCH-456,CUST-789,FRAUD,0.92,v1.2.3,2023-05-16T14:22:33Z\n" +
        "TX-11223,89.50,MERCH-789,CUST-123,NOT_FRAUD,0.05,v1.2.3,2023-05-17T09:15:22Z";
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch-results-${job.jobId}.csv`;
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
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center">
          <CheckCircleIcon className="h-6 w-6 text-green-500 mr-2" />
          <CardTitle>Batch Processing Complete</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg bg-muted p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Job ID</p>
              <p className="font-medium">{job.jobId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Completed On</p>
              <p className="font-medium">{new Date(job.timestamp).toLocaleString()}</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-sm text-primary">
          <FileTextIcon className="h-4 w-4" />
          <span>Results are ready for download</span>
        </div>
      </CardContent>
      <CardFooter className="flex flex-col sm:flex-row gap-3">
        <Button
          className="w-full sm:w-auto"
          onClick={handleDownload}
          disabled={isDownloading || !job.downloadUrl}
        >
          <Download className="mr-2 h-4 w-4" />
          {isDownloading ? "Downloading..." : "Download Results"}
        </Button>
        <Link href="/logs" className="w-full sm:w-auto">
          <Button variant="outline" className="w-full">
            <ExternalLinkIcon className="mr-2 h-4 w-4" />
            View Job Logs
          </Button>
        </Link>
        <Button 
          variant="ghost" 
          className="w-full sm:w-auto"
          onClick={onStartNew}
        >
          Start New Batch
        </Button>
      </CardFooter>
    </Card>
  );
}