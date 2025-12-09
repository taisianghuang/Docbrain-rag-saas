"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { chatbotService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RagMode, ChunkingStrategy, CreateChatbotPayload } from "@/types";
import { Bot, ArrowLeft, Cpu, Paintbrush, Loader2 } from "lucide-react";
import Link from "next/link";

export default function CreateChatbotPage() {
  const router = useRouter();

  // 表單初始狀態
  const [formData, setFormData] = useState<CreateChatbotPayload>({
    name: "",
    rag_config: {
      mode: RagMode.HYBRID,
      chunking_strategy: ChunkingStrategy.STANDARD,
      top_k: 5,
      temperature: 0.1,
      llm_model: "gpt-4o-mini",
    },
    widget_config: {
      title: "Help Assistant",
      primary_color: "#2563eb", // Default Blue
      welcome_message: "Hi! How can I help you today?",
    },
  });

  // 建立 Mutation
  const createMutation = useMutation({
    mutationFn: chatbotService.create,
    onSuccess: (data) => {
      // 成功後跳轉到該機器人的設定頁
      router.push(`/chatbots/${data.id}`);
    },
    onError: (error) => {
      console.error(error);
      alert("Failed to create chatbot. Please try again.");
    },
  });

  // 處理第一層欄位變更 (name)
  const handleRootChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, name: e.target.value }));
  };

  // 處理深層欄位變更 (rag_config, widget_config)
  const handleDeepChange = (
    section: "rag_config" | "widget_config",
    field: string,
    value: string | number
  ) => {
    setFormData((prev) => ({
      ...prev,
      [section]: { ...prev[section], [field]: value },
    }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      {/* 頂部導航 */}
      <div className="flex items-center space-x-4 mb-6">
        <Link href="/chatbots">
          <Button
            variant="ghost"
            size="sm"
            className="pl-0 hover:bg-transparent hover:text-primary">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to List
          </Button>
        </Link>
      </div>

      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
          Create New Chatbot
        </h1>
        <p className="text-muted-foreground mt-2">
          {"Configure your AI assistant's intelligence and appearance."}
        </p>
      </div>

      <div className="space-y-8">
        {/* 1. General Information */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              <CardTitle>General Information</CardTitle>
            </div>
            <CardDescription>
              Basic details about your assistant.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Chatbot Name
              </label>
              <Input
                placeholder="e.g. Legal Copilot, HR Helper"
                value={formData.name}
                onChange={handleRootChange}
                className="max-w-md"
              />
            </div>
          </CardContent>
        </Card>

        {/* 2. Intelligence (RAG) */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-purple-600" />
              <CardTitle>Intelligence Configuration</CardTitle>
            </div>
            <CardDescription>
              Define how the AI processes and retrieves your documents.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-2">
            {/* Retrieval Mode */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Retrieval Mode</label>
              <select
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={formData.rag_config.mode}
                onChange={(e) =>
                  handleDeepChange("rag_config", "mode", e.target.value)
                }>
                {Object.values(RagMode).map((m) => (
                  <option key={m} value={m}>
                    {m.toUpperCase()}
                  </option>
                ))}
              </select>
              <p className="text-[0.8rem] text-muted-foreground">
                Determines the search strategy (e.g. Hybrid searches both
                keywords and vectors).
              </p>
            </div>

            {/* Chunking Strategy */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Chunking Strategy</label>
              <select
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={formData.rag_config.chunking_strategy}
                onChange={(e) =>
                  handleDeepChange(
                    "rag_config",
                    "chunking_strategy",
                    e.target.value
                  )
                }>
                {Object.values(ChunkingStrategy).map((s) => (
                  <option key={s} value={s}>
                    {s.toUpperCase()}
                  </option>
                ))}
              </select>
              <p className="text-[0.8rem] text-muted-foreground">
                {
                  "How documents are split. 'Markdown' is best for structured text."
                }
              </p>
            </div>

            {/* Top K */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Top K Sources ({formData.rag_config.top_k})
              </label>
              <Input
                type="number"
                min={1}
                max={20}
                value={formData.rag_config.top_k}
                onChange={(e) =>
                  handleDeepChange(
                    "rag_config",
                    "top_k",
                    parseInt(e.target.value)
                  )
                }
              />
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Temperature ({formData.rag_config.temperature})
              </label>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={formData.rag_config.temperature}
                onChange={(e) =>
                  handleDeepChange(
                    "rag_config",
                    "temperature",
                    parseFloat(e.target.value)
                  )
                }
              />
              <p className="text-[0.8rem] text-muted-foreground">
                0 is precise/deterministic, 1 is creative.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 3. Appearance */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Paintbrush className="h-5 w-5 text-teal-600" />
              <CardTitle>Widget Appearance</CardTitle>
            </div>
            <CardDescription>
              Customize how the chat widget looks on your website.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Widget Title</label>
              <Input
                value={formData.widget_config.title}
                onChange={(e) =>
                  handleDeepChange("widget_config", "title", e.target.value)
                }
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Brand Color</label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  className="h-10 w-12 cursor-pointer rounded border border-gray-300 p-1"
                  value={formData.widget_config.primary_color}
                  onChange={(e) =>
                    handleDeepChange(
                      "widget_config",
                      "primary_color",
                      e.target.value
                    )
                  }
                />
                <Input
                  value={formData.widget_config.primary_color}
                  onChange={(e) =>
                    handleDeepChange(
                      "widget_config",
                      "primary_color",
                      e.target.value
                    )
                  }
                  className="font-mono uppercase"
                />
              </div>
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium">Welcome Message</label>
              <Input
                value={formData.widget_config.welcome_message}
                onChange={(e) =>
                  handleDeepChange(
                    "widget_config",
                    "welcome_message",
                    e.target.value
                  )
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-end gap-4 pt-4">
          <Link href="/chatbots">
            <Button variant="ghost">Cancel</Button>
          </Link>
          <Button
            size="lg"
            onClick={() => createMutation.mutate(formData)}
            disabled={createMutation.isPending || !formData.name}>
            {createMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Create Chatbot
          </Button>
        </div>
      </div>
    </div>
  );
}
