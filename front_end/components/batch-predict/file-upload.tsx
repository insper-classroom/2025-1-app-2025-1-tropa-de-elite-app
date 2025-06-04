"use client";

import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { UploadIcon, XIcon, AlertCircleIcon, FileIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isUploading?: boolean;
  progress?: number;
  onCancel?: () => void;
}

export function FileUpload({ 
  onFileSelect, 
  isUploading = false, 
  progress = 0,
  onCancel
}: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = (acceptedFiles: File[]) => {
    setError(null);
    if (acceptedFiles.length === 0) {
      return;
    }

    const selectedFile = acceptedFiles[0];
    
    // Check if file is a CSV
    if (selectedFile.type !== 'text/csv' && !selectedFile.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setFile(selectedFile);
    onFileSelect(selectedFile);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    disabled: isUploading,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1
  });

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
    setFile(null);
  };

  return (
    <div className="w-full">
      {!file && !isUploading ? (
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
            isDragActive
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50",
            error && "border-destructive/50 bg-destructive/5"
          )}
        >
          <input {...getInputProps()} />          <div className="flex flex-col items-center justify-center gap-2">
            <UploadIcon className="h-10 w-10 text-muted-foreground" />
            <h3 className="font-medium text-lg">Arraste ou solte o arquivo de transações aqui</h3>
            <p className="text-sm text-muted-foreground">
              ou clique para procurar um arquivo
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Apenas arquivos CSV são suportados
            </p>
          </div>
        </div>
      ) : (
        <div className="border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <FileIcon className="h-6 w-6 mr-3 text-primary" />
              <div>
                <p className="font-medium">{file?.name || "Processing file..."}</p>
                <p className="text-xs text-muted-foreground">
                  {file && `${(file.size / 1024).toFixed(2)} KB`}
                </p>
              </div>
            </div>
            {!isUploading && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleCancel}
                className="h-8 w-8"
              >
                <XIcon className="h-4 w-4" />
              </Button>
            )}
          </div>

          {isUploading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm mb-1">
                <span>Processing...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              <div className="flex justify-end mt-4">
                <Button variant="outline" size="sm" onClick={handleCancel}>
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-destructive text-sm mt-2">
          <AlertCircleIcon className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}