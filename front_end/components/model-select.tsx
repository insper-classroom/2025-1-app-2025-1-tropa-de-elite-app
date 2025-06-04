'use client';

import { useEffect, useState } from 'react';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue 
} from '@/components/ui/select';
import { getModels } from '@/lib/api';
import { Model } from '@/lib/types';
import { Loader2 } from 'lucide-react';

interface ModelSelectProps {
  onModelSelect: (modelId: string) => void;
  disabled?: boolean;
}

export default function ModelSelect({ 
  onModelSelect,
  disabled = false
}: ModelSelectProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true);
        const data = await getModels();
        setModels(data);
        setError(null);
      } catch (err) {
        setError('Falha ao carregar modelos');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  return (
    <div className="space-y-2">
      <Select 
        onValueChange={onModelSelect} 
        disabled={disabled || loading || models.length === 0}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder={
            loading 
              ? "Carregando modelos..." 
              : error 
                ? "Erro ao carregar modelos" 
                : models.length === 0 
                  ? "Nenhum modelo disponível" 
                  : "Selecione um modelo"
          } />
          {loading && <Loader2 className="h-4 w-4 animate-spin ml-2" />}
        </SelectTrigger>
        <SelectContent>
          {models.map((model) => (
            <SelectItem key={model.id} value={model.id}>
              {model.name} (v{model.version})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}
    </div>
  );
}