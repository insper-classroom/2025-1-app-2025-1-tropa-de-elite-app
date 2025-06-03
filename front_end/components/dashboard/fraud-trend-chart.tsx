"use client";

import { useState } from "react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Generate mock data for the chart
const generateDailyData = (days: number) => {
  const data = [];
  const date = new Date();
  date.setHours(0, 0, 0, 0);

  for (let i = days - 1; i >= 0; i--) {
    const currentDate = new Date(date);
    currentDate.setDate(currentDate.getDate() - i);
    
    const totalTransactions = Math.floor(Math.random() * 1000) + 500;
    const fraudRate = Math.random() * 0.05; // Up to 5% fraud rate
    
    data.push({
      date: currentDate.toISOString().split('T')[0],
      totalTransactions,
      fraudTransactions: Math.floor(totalTransactions * fraudRate),
      fraudRate: fraudRate * 100, // Convert to percentage
    });
  }
  
  return data;
};

const timeRanges = [
  { label: 'Last 7 Days', value: '7d', days: 7 },
  { label: 'Last 14 Days', value: '14d', days: 14 },
  { label: 'Last 30 Days', value: '30d', days: 30 },
];

export function FraudTrendChart() {
  const [timeRange, setTimeRange] = useState('7d');
  const selectedRange = timeRanges.find(range => range.value === timeRange) || timeRanges[0];
  const data = generateDailyData(selectedRange.days);

  return (
    <Card className="col-span-12 lg:col-span-8">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle>Fraud Trend Analysis</CardTitle>
          <CardDescription>
            Daily fraud detection rates and transaction volume
          </CardDescription>
        </div>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Select range" />
          </SelectTrigger>
          <SelectContent>
            {timeRanges.map((range) => (
              <SelectItem key={range.value} value={range.value}>
                {range.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent className="pt-4 h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-2))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--chart-2))" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="date" 
              className="text-xs text-muted-foreground"
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis className="text-xs text-muted-foreground" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))', 
                borderColor: 'hsl(var(--border))',
                color: 'hsl(var(--card-foreground))'
              }}
              formatter={(value: any, name: string) => {
                if (name === 'fraudRate') {
                  return [`${value.toFixed(2)}%`, 'Fraud Rate'];
                }
                return [value, name === 'totalTransactions' ? 'Total Transactions' : 'Fraud Transactions'];
              }}
              labelFormatter={(label) => {
                const date = new Date(label);
                return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
              }}
            />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="totalTransactions" 
              stroke="hsl(var(--chart-2))" 
              fillOpacity={1} 
              fill="url(#colorTotal)" 
              name="Total Transactions"
            />
            <Area 
              type="monotone" 
              dataKey="fraudTransactions" 
              stroke="hsl(var(--destructive))" 
              fillOpacity={1} 
              fill="url(#colorFraud)" 
              name="Fraud Transactions"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}