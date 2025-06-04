'use client';

import { Transaction } from '@/lib/types';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow 
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface LogsTableProps {
  transactions: Transaction[];
  loading?: boolean;
}

export default function LogsTable({ 
  transactions, 
  loading = false 
}: LogsTableProps) {
  if (loading) {
    return <LogsTableSkeleton />;
  }

  if (transactions.length === 0) {
    return (
      <div className="text-center py-8 border rounded-md">
        <p className="text-gray-500">Nenhuma transação para exibir</p>
      </div>
    );
  }

  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID da Transação</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Data/Hora</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((transaction) => (
            <TableRow key={transaction.transactionId}>
              <TableCell className="font-mono">
                {transaction.transactionId}
              </TableCell>
              <TableCell>
                <StatusBadge status={transaction.status} />
              </TableCell>
              <TableCell className="text-gray-500">
                {formatTimestamp(transaction.timestamp)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function StatusBadge({ status }: { status: 'approved' | 'rejected' }) {
  const text = status === 'approved' ? 'Aprovado' : 'Reprovado';
  
  return (
    <Badge
      variant="outline"
      className={`
        ${status === 'approved' 
          ? 'text-green-700 bg-green-50 border-green-200'
          : 'text-red-700 bg-red-50 border-red-200'
        }
      `}
    >
      {text}
    </Badge>
  );
}

function formatTimestamp(timestamp: string): string {
  try {
    return format(new Date(timestamp), 'PPp', { locale: ptBR });
  } catch (error) {
    return timestamp;
  }
}

function LogsTableSkeleton() {
  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID da Transação</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Data/Hora</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 5 }).map((_, i) => (
            <TableRow key={i}>
              <TableCell>
                <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
              </TableCell>
              <TableCell>
                <div className="h-6 w-20 bg-gray-200 rounded animate-pulse" />
              </TableCell>
              <TableCell>
                <div className="h-4 w-28 bg-gray-200 rounded animate-pulse" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}