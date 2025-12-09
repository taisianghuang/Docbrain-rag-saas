"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { chatbotService, documentService } from "@/lib/api";
import {
  Chatbot,
  CreateChatbotPayload,
  RagMode,
  ChunkingStrategy,
  RagConfig,
  WidgetConfig,
} from "@/types";
import { toast } from "sonner";

// UI Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Lock, AlertTriangle, Save, Loader2 } from "lucide-react";

interface ConfigTabProps {
  chatbot: Chatbot;
}

export function ConfigTab({ chatbot }: Readonly<ConfigTabProps>) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Chatbot>({
    ...chatbot,
    rag_config: chatbot.rag_config || {
      mode: "vector",
      chunking_strategy: "standard",
      llm_model: "gpt-4o-mini",
      top_k: 5,
      temperature: 0.1,
    },
    widget_config: chatbot.widget_config || {
      title: "Chat Assistant",
      primary_color: "#2563eb",
      welcome_message: "Hi! How can I help you today?",
    },
  });
  const [isDirty, setIsDirty] = useState(false);

  // 檢查是否有文件存在 (若有，鎖定 RAG 設定)
  const { data: documents } = useQuery({
    queryKey: ["documents", chatbot.id],
    queryFn: () => documentService.list(chatbot.id),
  });
  const hasDocuments = documents && documents.length > 0;

  // 更新 Mutation
  const updateMutation = useMutation({
    mutationFn: (data: Partial<CreateChatbotPayload>) =>
      chatbotService.update(chatbot.id, data),
    onSuccess: (updatedBot) => {
      queryClient.setQueryData(["chatbot", chatbot.id], updatedBot);
      queryClient.invalidateQueries({ queryKey: ["chatbots"] });
      setIsDirty(false);
      toast.success("Settings saved successfully!");
    },
    onError: (err) => {
      toast.error("Failed to save settings.");
      console.error(err);
    },
  });

  const handleChange = (
    section: "rag_config" | "widget_config" | null,
    field: string,
    value: string | number | boolean
  ) => {
    setIsDirty(true);
    setFormData((prev) => {
      if (section) {
        return {
          ...prev,
          [section]: {
            ...(prev[section] as RagConfig | WidgetConfig),
            [field]: value,
          },
        };
      } else {
        return {
          ...prev,
          [field]: value,
        };
      }
    });
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* General & Widget Settings */}
      <Card>
        <CardHeader>
          <CardTitle>General & Appearance</CardTitle>
          <CardDescription>
            {"Customize your chatbot's identity and widget look."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="chatbot-name" className="text-sm font-medium">
              Chatbot Name
            </label>
            <Input
              id="chatbot-name"
              value={formData.name}
              onChange={(e) => handleChange(null, "name", e.target.value)}
            />
          </div>

          <Separator className="my-2" />

          <div className="space-y-2">
            <label htmlFor="widget-title" className="text-sm font-medium">
              Widget Title
            </label>
            <Input
              id="widget-title"
              value={formData.widget_config.title}
              onChange={(e) =>
                handleChange("widget_config", "title", e.target.value)
              }
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="welcome-message" className="text-sm font-medium">
              Welcome Message
            </label>
            <Input
              id="welcome-message"
              value={formData.widget_config.welcome_message}
              onChange={(e) =>
                handleChange("widget_config", "welcome_message", e.target.value)
              }
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="primary-color" className="text-sm font-medium">
              Brand Color
            </label>
            <div className="flex items-center gap-3">
              <input
                id="primary-color"
                type="color"
                className="h-10 w-12 cursor-pointer rounded border border-input p-1"
                value={formData.widget_config.primary_color}
                onChange={(e) =>
                  handleChange("widget_config", "primary_color", e.target.value)
                }
              />
              <Input
                id="primary-color-hex"
                className="font-mono uppercase w-32"
                value={formData.widget_config.primary_color}
                onChange={(e) =>
                  handleChange("widget_config", "primary_color", e.target.value)
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* RAG Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            RAG Configuration
            {hasDocuments && (
              <Badge
                variant="secondary"
                className="text-xs bg-amber-100 text-amber-800 hover:bg-amber-100">
                <Lock className="w-3 h-3 mr-1" /> Locked
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            Configure the AI brain. Core indexing settings are locked when
            documents exist.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {hasDocuments && (
            <Alert
              variant="default"
              className="bg-amber-50 dark:bg-amber-900/20 border-amber-200 text-amber-800 dark:text-amber-200 py-3">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Settings Locked</AlertTitle>
              <AlertDescription className="text-xs">
                To change Chunking Strategy or Retrieval Mode, you must delete
                all documents from the Knowledge Base first.
              </AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="retrieval-mode" className="text-sm font-medium">
                Retrieval Mode
              </label>
              <Select
                disabled={Boolean(hasDocuments)}
                value={formData.rag_config.mode}
                onValueChange={(val) =>
                  handleChange("rag_config", "mode", val)
                }>
                <SelectTrigger id="retrieval-mode">
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(RagMode).map((m) => (
                    <SelectItem key={m} value={m}>
                      {m.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label htmlFor="chunking-select" className="text-sm font-medium">
                Chunking
              </label>
              <Select
                disabled={Boolean(hasDocuments)}
                value={formData.rag_config.chunking_strategy}
                onValueChange={(val) =>
                  handleChange("rag_config", "chunking_strategy", val)
                }>
                <SelectTrigger id="chunking-select">
                  <SelectValue placeholder="Select strategy" />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(ChunkingStrategy).map((m) => (
                    <SelectItem key={m} value={m}>
                      {m.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          <div className="space-y-2">
            <label htmlFor="llm-model-select" className="text-sm font-medium">
              LLM Model
            </label>
            <Select
              value={formData.rag_config.llm_model || "gpt-4o-mini"}
              onValueChange={(val) =>
                handleChange("rag_config", "llm_model", val)
              }>
              <SelectTrigger id="llm-model-select">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Model used for generating chat responses
            </p>
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="cfg-top-k" className="text-sm font-medium">
                Top K Sources ({formData.rag_config.top_k})
              </label>
              <Input
                id="cfg-top-k"
                type="number"
                min={1}
                max={20}
                value={formData.rag_config.top_k}
                onChange={(e) =>
                  handleChange(
                    "rag_config",
                    "top_k",
                    Number.parseInt(e.target.value)
                  )
                }
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="cfg-temperature" className="text-sm font-medium">
                Temperature ({formData.rag_config.temperature})
              </label>
              <Input
                id="cfg-temperature"
                type="number"
                step={0.1}
                min={0}
                max={1}
                value={formData.rag_config.temperature}
                onChange={(e) =>
                  handleChange(
                    "rag_config",
                    "temperature",
                    Number.parseFloat(e.target.value)
                  )
                }
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="bg-muted/30 border-t flex justify-end p-4">
          <Button
            onClick={() => updateMutation.mutate(formData)}
            disabled={!isDirty || updateMutation.isPending}>
            {updateMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            <Save className="mr-2 h-4 w-4" /> Save Changes
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
