"use client";

import { useState, useEffect } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { FileUpload } from "@/components/batch-predict/file-upload";
import { BatchResult } from "@/components/batch-predict/batch-result";
import { api } from "@/lib/api";
import { BatchJob } from "@/types";
import { toast } from "sonner";
import { AlertCircleIcon } from "lucide-react";

export default function BatchPredictPage() {
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<BatchJob | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    const checkJobStatus = async () => {
      if (!job || job.status === 'completed' || job.status === 'failed') {
        if (interval) clearInterval(interval);
        return;
      }
      
      try {
        const updatedJob = await api.getBatchJobStatus(job.jobId);
        
        // Only update state if there are actual changes
        if (updatedJob.progress !== job.progress) {
          setProgress(updatedJob.progress);
        }
        
        if (updatedJob.status !== job.status) {
          setJob(updatedJob);
          
          if (updatedJob.status === 'completed') {
            toast.success('Batch processing complete!');
            clearInterval(interval);
          } else if (updatedJob.status === 'failed') {
            setError('Batch processing failed. Please try again.');
            clearInterval(interval);
          }
        }
      } catch (error) {
        console.error('Error checking job status:', error);
        setError('Failed to check job status');
        clearInterval(interval);
      }
    };
    
    if (job && job.status === 'processing') {
      // Initial check
      checkJobStatus();
      // Set up polling interval
      interval = setInterval(checkJobStatus, 2000);
    }
    
    // Cleanup function
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [job?.jobId, job?.status]); // Only depend on specific job properties

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    
    try {
      setProgress(0);
      const { jobId } = await api.submitBatchJob(file);
      setJob({
        jobId,
        progress: 0,
        status: 'processing',
        timestamp: new Date().toISOString(),
        userId: 'current-user', // Would come from auth in real app
      });
      toast.info('Batch processing started');
    } catch (error) {
      console.error('Error submitting batch job:', error);
      setError('Failed to submit batch job. Please try again.');
    }
  };

  const handleCancel = () => {
    setJob(null);
    setFile(null);
    setProgress(0);
    setError(null);
  };

  // Separate useEffect for handling file upload
  useEffect(() => {
    if (file && !job) {
      handleUpload();
    }
  }, [file]); // Only depend on file changes

  return (
    <div className="container py-6">
      <PageHeader
        title="Batch Transaction Analysis"
        description="Upload and analyze multiple transactions at once"
      />

      <div className="mt-8 max-w-3xl mx-auto">
        {error && (
          <div className="mb-6 p-4 border border-destructive/50 bg-destructive/10 rounded-md flex items-center gap-2 text-destructive">
            <AlertCircleIcon className="h-5 w-5" />
            <p>{error}</p>
          </div>
        )}

        {job && job.status === 'completed' ? (
          <BatchResult job={job} onStartNew={handleCancel} />
        ) : (
          <FileUpload 
            onFileSelect={handleFileSelect}
            isUploading={!!job && job.status === 'processing'}
            progress={progress}
            onCancel={handleCancel}
          />
        )}

        <div className="mt-8 text-sm text-muted-foreground">
          <h3 className="font-medium text-foreground mb-2">Batch Processing Information:</h3>
          <ul className="list-disc pl-5 space-y-1">
            <li>Upload a CSV file with transaction data for bulk analysis</li>
            <li>The CSV should have headers and include all relevant transaction attributes</li>
            <li>Maximum file size: 10MB</li>
            <li>Processing time depends on the number of transactions (typically 1-2 minutes)</li>
            <li>Results will include the original data plus fraud scores and decisions</li>
          </ul>
        </div>
      </div>
    </div>
  );
}