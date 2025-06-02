'use client';

import { useAppState } from '@/lib/app-context';
import { ProcessingLogs } from '@/components/ui/processing-logs';

export default function ProcessingStatus() {
  const { processing } = useAppState();
  
  return (
    <>
      <ProcessingLogs processing={processing} />
    </>
  );
}
