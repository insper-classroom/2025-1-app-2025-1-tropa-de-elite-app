import { ShieldAlertIcon, Wallet, AlertCircleIcon, Clock } from "lucide-react";
import { StatsCard } from "@/components/dashboard/stats-card";

export function FraudStatisticsGrid() {
  return (
    <>
      <StatsCard
        title="Total Transactions"
        value="18,492"
        description="Last 24 hours"
        icon={<Wallet className="h-4 w-4" />}
        trend={{ value: 12, label: "from yesterday", positive: true }}
        className="col-span-6 sm:col-span-3"
      />
      <StatsCard
        title="Fraud Rate"
        value="2.4%"
        description="Last 24 hours"
        icon={<ShieldAlertIcon className="h-4 w-4" />}
        trend={{ value: 0.3, label: "from yesterday", positive: false }}
        className="col-span-6 sm:col-span-3"
      />
      <StatsCard
        title="High Risk Alerts"
        value="48"
        description="Requiring review"
        icon={<AlertCircleIcon className="h-4 w-4" />}
        trend={{ value: 5, label: "from yesterday", positive: false }}
        className="col-span-6 sm:col-span-3"
      />
      <StatsCard
        title="Avg. Response Time"
        value="230ms"
        description="API response time"
        icon={<Clock className="h-4 w-4" />}
        trend={{ value: 15, label: "improvement", positive: true }}
        className="col-span-6 sm:col-span-3"
      />
    </>
  );
}