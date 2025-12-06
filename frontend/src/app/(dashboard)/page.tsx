"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { statsService } from "@/lib/api";
import { Activity, MessageSquare, Cloud, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// 1. 定義介面
interface StatCardProps {
  title: string;
  value: string | number;
  subtext: string;
  icon: React.ElementType; // Lucide icon 是一個 Component Type
  className?: string;
}

// 定義統計卡片元件
const StatCard = ({
  title,
  value,
  subtext,
  icon: Icon,
  className,
}: StatCardProps) => (
  <Card className={className}>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <Icon className="h-4 w-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      <p className="text-xs text-muted-foreground">{subtext}</p>
    </CardContent>
  </Card>
);

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: statsService.getOverview,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-muted-foreground">Loading Dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Dashboard Overview
        </h2>
        <p className="text-muted-foreground">
          Real-time metrics for your AI infrastructure.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Total Traffic"
          value={stats?.chatbot_traffic?.toLocaleString() ?? 0}
          subtext="Total messages processed"
          icon={MessageSquare}
        />
        <StatCard
          title="OpenAI Usage"
          value={`$${stats?.openai_usage ?? 0}`}
          subtext="Current billing cycle cost"
          icon={DollarSign}
        />
        <StatCard
          title="LlamaCloud Ops"
          value={stats?.llama_cloud_ops?.toLocaleString() ?? 0}
          subtext="Parsing & indexing operations"
          icon={Cloud}
        />
      </div>

      {/* Activity Chart Area (Mock Visual) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Traffic History (Last 7 Days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] w-full flex items-end justify-between gap-2 px-4 pt-8">
            {stats?.history.map((item, idx) => {
              // 簡單計算高度百分比，最高 100%
              const height = `${Math.min((item.value / 300) * 100, 100)}%`;
              return (
                <div
                  key={idx}
                  className="group relative flex flex-1 flex-col items-center gap-2">
                  <div
                    className="w-full rounded-t-md bg-primary/20 transition-all group-hover:bg-primary/40"
                    style={{ height }}>
                    {/* Tooltip on hover */}
                    <div className="absolute -top-10 left-1/2 -translate-x-1/2 rounded bg-popover px-2 py-1 text-xs text-popover-foreground opacity-0 shadow-sm transition-opacity group-hover:opacity-100 border">
                      {item.value} msgs
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {item.date}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
