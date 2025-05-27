"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { PredictionResult } from "@/types";
import { CheckCircle2Icon, AlertCircleIcon, InfoIcon } from "lucide-react";
import { useState } from "react";

interface PredictionResultCardProps {
  result: PredictionResult;
}

export function PredictionResultCard({ result }: PredictionResultCardProps) {
  const [open, setOpen] = useState(false);
  const isFraud = result.decision === "FRAUD";
  const formattedScore = (result.score * 100).toFixed(2);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Fraud Analysis Result</span>
          <Badge 
            variant={isFraud ? "destructive" : "success"}
            className="ml-2 text-xs font-semibold uppercase tracking-wide px-3 py-1"
          >
            {isFraud ? "FRAUD" : "NOT FRAUD"}
          </Badge>
        </CardTitle>
        <CardDescription>
          Analysis completed on {new Date(result.timestamp).toLocaleString()}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-muted p-3">
            <div className="text-sm font-medium text-muted-foreground mb-1">Score</div>
            <div className="text-2xl font-bold flex items-center">
              {formattedScore}%
              {isFraud ? (
                <AlertCircleIcon className="ml-2 h-5 w-5 text-destructive" />
              ) : (
                <CheckCircle2Icon className="ml-2 h-5 w-5 text-green-500" />
              )}
            </div>
          </div>
          <div className="rounded-lg bg-muted p-3">
            <div className="text-sm font-medium text-muted-foreground mb-1">Model Version</div>
            <div className="text-2xl font-bold">{result.version}</div>
          </div>
        </div>

        <div className="flex items-center text-sm text-muted-foreground">
          <InfoIcon className="mr-2 h-4 w-4" />
          {isFraud 
            ? "This transaction has been flagged as potentially fraudulent."
            : "This transaction appears to be legitimate."
          }
        </div>
      </CardContent>
      <CardFooter>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="w-full">View Details</Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Detailed Analysis</DialogTitle>
              <DialogDescription>
                The following attributes were analyzed to reach this decision.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="rounded-md bg-muted p-4">
                <h3 className="mb-2 font-semibold">Key Factors</h3>
                <div className="space-y-2">
                  <div className="grid grid-cols-12 text-sm">
                    <div className="col-span-4 font-medium">Transaction Amount</div>
                    <div className="col-span-4">${result.attributes?.amount?.toFixed(2) ?? 'N/A'}</div>
                    <div className="col-span-4 text-muted-foreground">
                      {result.attributes?.amount > 500 ? "Higher than usual" : "Within normal range"}
                    </div>
                  </div>
                  <div className="grid grid-cols-12 text-sm">
                    <div className="col-span-4 font-medium">Location</div>
                    <div className="col-span-4">{result.attributes?.location ?? 'N/A'}</div>
                    <div className="col-span-4 text-muted-foreground">
                      {result.attributes?.location === "New York, USA" 
                        ? "Matches customer profile" 
                        : "Unusual location for this customer"}
                    </div>
                  </div>
                  <div className="grid grid-cols-12 text-sm">
                    <div className="col-span-4 font-medium">Device</div>
                    <div className="col-span-4">{result.attributes.deviceId}</div>
                    <div className="col-span-4 text-muted-foreground">
                      {result.attributes.deviceId.includes("iPhone") 
                        ? "Recognized device" 
                        : "New device"}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="mb-2 font-semibold">All Attributes</h3>
                <div className="rounded-md border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted">
                        <th className="px-4 py-2 text-left">Attribute</th>
                        <th className="px-4 py-2 text-left">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(result.attributes).map(([key, value]) => (
                        <tr key={key} className="border-b last:border-b-0">
                          <td className="px-4 py-2 font-medium">{key}</td>
                          <td className="px-4 py-2">{String(value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  );
}