'use client';

import { useState, useRef, ChangeEvent, DragEvent } from 'react';
import { UploadCloud } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploaderProps {
  onFileSelected: (file: File) => void;
  accept?: string;
  maxSize?: number;
  className?: string;
}

export default function FileUploader({
  onFileSelected,
  accept = '.csv',
  maxSize = 5 * 1024 * 1024, // 5MB default
  className,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setError(null);
    
    if (accept && !file.name.toLowerCase().endsWith('.csv')) {
      setError('Por favor, faça upload de um arquivo CSV');
      return;
    }
    
    if (file.size > maxSize) {
      setError(`Tamanho do arquivo excede o limite (${maxSize / (1024 * 1024)}MB)`);
      return;
    }
    
    setFileName(file.name);
    onFileSelected(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    inputRef.current?.click();
  };

  return (
    <div
      className={cn(
        'relative border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center transition-colors',
        isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50',
        className
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={triggerFileInput}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={accept}
        onChange={handleFileChange}
      />
      
      <div className="flex flex-col items-center text-center">
        <UploadCloud className="h-12 w-12 text-gray-400 mb-3" />
        
        {fileName ? (
          <>
            <p className="text-sm font-medium text-gray-900">{fileName}</p>
            <p className="text-xs text-gray-500 mt-1">
              Clique ou arraste para substituir
            </p>
          </>
        ) : (
          <>
            <p className="text-sm font-medium text-gray-900">
              Arraste e solte ou clique para fazer upload
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Apenas arquivos CSV até {maxSize / (1024 * 1024)}MB
            </p>
          </>
        )}
        
        {error && (
          <p className="text-xs text-red-500 mt-2">{error}</p>
        )}
      </div>
    </div>
  );
}