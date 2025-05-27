"use client";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { FraudStatisticsGrid } from "@/components/dashboard/fraud-statistics-grid";
import { FraudTrendChart } from "@/components/dashboard/fraud-trend-chart";
import { ModelPerformanceCard } from "@/components/dashboard/model-performance-card";
import Link from "next/link";
import { LineChart, ActivityIcon } from "lucide-react";

export default function Home() {
  return (
    <div className="container py-6">
      <PageHeader
        title="Fraud Analytics Dashboard"
        description="Real-time fraud detection metrics and analysis"
        actions={
          <div className="flex gap-3">
            <Link href="/single-predict">
              <Button>
                <ActivityIcon className="mr-2 h-4 w-4" />
                Analyze Transaction
              </Button>
            </Link>
            <Link href="/logs">
              <Button variant="outline">
                <LineChart className="mr-2 h-4 w-4" />
                View Logs
              </Button>
            </Link>
          </div>
        }
      />

      <div className="grid grid-cols-12 gap-6 mt-6">
        <FraudStatisticsGrid />
      </div>

      <div className="grid grid-cols-12 gap-6 mt-6">
        <FraudTrendChart />
        <ModelPerformanceCard />
      </div>
    </div>
  );
}