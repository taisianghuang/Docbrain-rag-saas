"use client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, MessageSquare, Zap, Users } from "lucide-react";

const data = [
  { name: "Mon", chats: 40 },
  { name: "Tue", chats: 30 },
  { name: "Wed", chats: 20 },
  { name: "Thu", chats: 27 },
  { name: "Fri", chats: 18 },
  { name: "Sat", chats: 23 },
  { name: "Sun", chats: 34 },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Dashboard Overview
        </h1>
        <p className="text-slate-500">
          Monitor your RAG performance and usage.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            title: "Total Documents",
            value: "124",
            icon: FileText,
            color: "text-blue-600",
            change: "+12% from last month",
          },
          {
            title: "Total Conversations",
            value: "2,543",
            icon: MessageSquare,
            color: "text-green-600",
            change: "+5% from last month",
          },
          {
            title: "Avg Response Time",
            value: "1.2s",
            icon: Zap,
            color: "text-amber-600",
            change: "-0.3s improvement",
          },
          {
            title: "Active Users",
            value: "573",
            icon: Users,
            color: "text-purple-600",
            change: "+20% from last month",
          },
        ].map((stat, i) => (
          <Card key={i}>
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">
                  {stat.title}
                </p>
                <h3 className="text-2xl font-bold text-slate-900 mt-1">
                  {stat.value}
                </h3>
                <p className="text-xs text-slate-400 mt-1">{stat.change}</p>
              </div>
              <div className={`p-3 bg-slate-50 rounded-lg ${stat.color}`}>
                <stat.icon size={24} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Chat Volume (Last 7 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#e2e8f0"
                  />
                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#64748b", fontSize: 12 }}
                    dy={10}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#64748b", fontSize: 12 }}
                  />
                  <Tooltip
                    cursor={{ fill: "#f1f5f9" }}
                    contentStyle={{
                      borderRadius: "8px",
                      border: "none",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                  />
                  <Bar
                    dataKey="chats"
                    fill="#2563eb"
                    radius={[4, 4, 0, 0]}
                    barSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {[
                {
                  text: 'New document uploaded: "Q3_Financials.pdf"',
                  time: "2 mins ago",
                  type: "upload",
                },
                {
                  text: "Widget embedded on pricing page",
                  time: "1 hour ago",
                  type: "system",
                },
                {
                  text: "High volume of queries detected",
                  time: "4 hours ago",
                  type: "alert",
                },
                {
                  text: "System maintenance completed",
                  time: "Yesterday",
                  type: "system",
                },
              ].map((item, i) => (
                <div key={i} className="flex gap-3 items-start">
                  <div
                    className={`mt-1 w-2 h-2 rounded-full ${
                      item.type === "upload"
                        ? "bg-blue-500"
                        : item.type === "alert"
                        ? "bg-red-500"
                        : "bg-slate-300"
                    }`}
                  />
                  <div>
                    <p className="text-sm text-slate-800">{item.text}</p>
                    <p className="text-xs text-slate-400">{item.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
