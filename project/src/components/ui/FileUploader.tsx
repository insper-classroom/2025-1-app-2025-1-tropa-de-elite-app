import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import clsx from 'clsx';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
}

const FileUploader: React.FC<FileUploaderProps> = ({
  onFileSelect,
  accept = {
    'application/octet-stream': ['.feather'],
    'text/csv': ['.csv'],
    'application/vnd.apache.parquet': ['.parquet'],
  },
  maxSize = 104857600, // 100MB
}) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragReject, fileRejections } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles: 1,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
  });

  const hasError = isDragReject || fileRejections.length > 0;

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-6 cursor-pointer transition-all duration-200 flex flex-col items-center justify-center text-center',
          {
            'border-primary-400 bg-primary-50': isDragActive && !hasError,
            'border-danger-500 bg-danger-50': hasError,
            'border-gray-300 hover:border-primary-400 hover:bg-primary-50': !isDragActive && !hasError,
            'bg-gray-50': !isDragActive && !hasError && !selectedFile,
            'bg-green-50 border-green-300': selectedFile && !isDragActive && !hasError,
          }
        )}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center space-y-2">
          {selectedFile ? (
            <>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-10 w-10 text-green-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <p className="text-sm font-medium text-gray-900">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <p className="text-xs text-gray-500">
                Arraste outro arquivo para substituir
              </p>
            </>
          ) : hasError ? (
            <>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-10 w-10 text-danger-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-sm font-medium text-danger-700">
                Arquivo inválido
              </p>
              <p className="text-xs text-danger-500">
                Arquivos CSV, Feather ou Parquet são permitidos (máx. 100MB)
              </p>
            </>
          ) : (
            <>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-10 w-10 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="text-sm font-medium text-gray-700">
                Arraste e solte o arquivo aqui
              </p>
              <p className="text-xs text-gray-500">
                CSV, Feather ou Parquet (máx. 100MB)
              </p>
            </>
          )}
        </div>
      </div>

      {fileRejections.length > 0 && (
        <p className="mt-2 text-xs text-danger-500">
          {fileRejections[0].errors[0].message}
        </p>
      )}
    </div>
  );
};

export default FileUploader;