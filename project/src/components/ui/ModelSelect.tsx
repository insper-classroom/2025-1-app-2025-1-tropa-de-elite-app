import React from 'react';
import { Model } from '@/types';

interface ModelSelectProps {
  models: Model[];
  selectedModel: string;
  onSelect: (modelId: string) => void;
  isLoading: boolean;
}

const ModelSelect: React.FC<ModelSelectProps> = ({
  models,
  selectedModel,
  onSelect,
  isLoading,
}) => {
  return (
    <div className="w-full">
      <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 mb-1">
        Selecionar Modelo
      </label>
      <div className="relative">
        <select
          id="model-select"
          value={selectedModel}
          onChange={(e) => onSelect(e.target.value)}
          disabled={isLoading || models.length === 0}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 bg-white py-2 pl-3 pr-10 text-base disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          {models.length === 0 && (
            <option value="">Nenhum modelo disponível</option>
          )}
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name} (v{model.version})
            </option>
          ))}
        </select>
        {isLoading && (
          <div className="absolute right-2 top-2">
            <svg className="animate-spin h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelSelect;