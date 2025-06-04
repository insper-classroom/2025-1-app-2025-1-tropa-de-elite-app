"use client";

import { useEffect, useState } from "react";
import { ArrowUpIcon, ArrowDownIcon, Activity } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api-integration-ready";

export function ModelPerformanceCard() {
  const [modelInfo, setModelInfo] = useState({ version: "loading..." });
  const [stats, setStats] = useState({
    precision: 0,
    recall: 0,
    f1Score: 0,
    lastUpdated: "",
    trend: "stable" as "up" | "down" | "stable",
  });

  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        const info = await api.getCurrentModel();
        setModelInfo(info);
        
        // Mock statistics since we don't have real data
        setStats({
          precision: 0.92,
          recall: 0.88,
          f1Score: 0.90,
          lastUpdated: new Date().toISOString(),
          trend: "up",
        });
      } catch (error) {
        console.error("Error fetching model info:", error);
      }
    };

    fetchModelInfo();
  }, []);

  const getTrendIcon = () => {
    switch (stats.trend) {
      case "up":
        return <ArrowUpIcon className="h-4 w-4 text-green-500" />;
      case "down":
        return <ArrowDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <Card className="col-span-12 lg:col-span-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-xl font-medium">
          Current Model
        </CardTitle>
        <CardDescription>
          Version: {modelInfo.version}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Precision</span>
              <span className="font-medium flex items-center">
                {(stats.precision * 100).toFixed(1)}%
                {getTrendIcon()}
              </span>
            </div>
            <Progress value={stats.precision * 100} className="h-2" />
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Recall</span>
              <span className="font-medium">{(stats.recall * 100).toFixed(1)}%</span>
            </div>
            <Progress value={stats.recall * 100} className="h-2" />
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">F1 Score</span>
              <span className="font-medium">{(stats.f1Score * 100).toFixed(1)}%</span>
            </div>
            <Progress value={stats.f1Score * 100} className="h-2" />
          </div>
          
          <div className="rounded-md bg-muted p-3 flex items-center gap-2 text-sm">
            <Activity className="h-4 w-4 text-primary" />
            <span>
              Updated {new Date(stats.lastUpdated).toLocaleDateString()}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}