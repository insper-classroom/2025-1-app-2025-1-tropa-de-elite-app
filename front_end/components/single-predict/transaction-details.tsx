"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Transaction } from "@/types";

interface TransactionDetailsProps {
  transaction: Transaction;
}

export function TransactionDetails({ transaction }: TransactionDetailsProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Transaction Details</CardTitle>
        <CardDescription>
          ID: {transaction.id} | {new Date(transaction.timestamp).toLocaleString()}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b">
                <td className="px-4 py-2 font-medium bg-muted">Amount</td>
                <td className="px-4 py-2">${transaction.amount.toFixed(2)}</td>
              </tr>
              <tr className="border-b">
                <td className="px-4 py-2 font-medium bg-muted">Merchant ID</td>
                <td className="px-4 py-2">{transaction.merchantId}</td>
              </tr>
              <tr className="border-b">
                <td className="px-4 py-2 font-medium bg-muted">Customer ID</td>
                <td className="px-4 py-2">{transaction.customerId}</td>
              </tr>
              <tr className="border-b">
                <td className="px-4 py-2 font-medium bg-muted">Card Type</td>
                <td className="px-4 py-2">{transaction.cardType}</td>
              </tr>
              <tr className="border-b">
                <td className="px-4 py-2 font-medium bg-muted">IP Address</td>
                <td className="px-4 py-2">{transaction.ipAddress}</td>
              </tr>
              <tr className="border-b">
                <td className="px-4 py-2 font-medium bg-muted">Device ID</td>
                <td className="px-4 py-2">{transaction.deviceId}</td>
              </tr>
              <tr>
                <td className="px-4 py-2 font-medium bg-muted">Location</td>
                <td className="px-4 py-2">{transaction.location}</td>
              </tr>
              {Object.entries(transaction || {}).map(([key, value]) => {
                // Skip already displayed fields and internal fields
                if (['id', 'timestamp', 'amount', 'merchantId', 'customerId', 'cardType', 'ipAddress', 'deviceId', 'location'].includes(key)) {
                  return null;
                }
                return (
                  <tr key={key} className="border-b last:border-b-0">
                    <td className="px-4 py-2 font-medium bg-muted">
                      {key.charAt(0).toUpperCase() + key.slice(1)}
                    </td>
                    <td className="px-4 py-2">{String(value)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}