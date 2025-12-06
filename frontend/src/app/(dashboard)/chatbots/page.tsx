"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { chatbotService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Plus,
  MessageSquare,
  Settings2,
  Activity,
  ArrowRight,
  Bot,
} from "lucide-react";

export default function ChatbotListPage() {
  const { data: chatbots, isLoading } = useQuery({
    queryKey: ["chatbots"],
    queryFn: chatbotService.list,
  });

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <span className="text-muted-foreground animate-pulse">
          Loading chatbots...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 頁面標題與動作區 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
            My Chatbots
          </h2>
          <p className="text-muted-foreground">
            Manage and configure your AI assistants.
          </p>
        </div>
        <Link href="/chatbots/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> New Chatbot
          </Button>
        </Link>
      </div>

      {/* 列表內容 */}
      {chatbots?.length === 0 ? (
        // Empty State (無資料時的顯示)
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center animate-in fade-in-50">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 mb-4">
            <Bot className="h-6 w-6 text-primary" />
          </div>
          <h3 className="text-lg font-semibold">No chatbots created yet</h3>
          <p className="mb-4 text-sm text-muted-foreground max-w-sm">
            Create your first AI assistant to start ingesting documents and
            chatting.
          </p>
          <Link href="/chatbots/new">
            <Button variant="outline">Create your first chatbot</Button>
          </Link>
        </div>
      ) : (
        // Grid Layout (卡片列表)
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {chatbots?.map((bot) => (
            <Card
              key={bot.id}
              className="group hover:shadow-md transition-shadow flex flex-col">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-lg"
                    style={{
                      backgroundColor: `${bot.widget_config.primary_color}20`, // 20 = 12% opacity hex
                      color: bot.widget_config.primary_color,
                    }}>
                    <MessageSquare size={20} />
                  </div>
                  <Badge
                    variant={bot.is_active ? "default" : "secondary"}
                    className={
                      bot.is_active ? "bg-green-500 hover:bg-green-600" : ""
                    }>
                    {bot.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <CardTitle className="mt-4 text-xl">{bot.name}</CardTitle>
              </CardHeader>

              <CardContent className="flex-1 pb-3">
                <p className="text-sm text-muted-foreground line-clamp-2 min-h-[2.5rem]">
                  {bot.widget_config.welcome_message ||
                    "No description provided."}
                </p>

                <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Settings2 className="h-3.5 w-3.5" />
                    <span className="capitalize">{bot.rag_config.mode}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Activity className="h-3.5 w-3.5" />
                    <span>Top-k: {bot.rag_config.top_k}</span>
                  </div>
                </div>
              </CardContent>

              <CardFooter className="pt-3 border-t bg-muted/20">
                <Link href={`/chatbots/${bot.id}`} className="w-full">
                  <Button
                    variant="ghost"
                    className="w-full justify-between hover:bg-white dark:hover:bg-slate-800">
                    Configure
                    <ArrowRight className="h-4 w-4 ml-2 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
