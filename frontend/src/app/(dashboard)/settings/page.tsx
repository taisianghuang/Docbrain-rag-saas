"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { settingsService } from "@/lib/api";
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
import { Separator } from "@/components/ui/separator";
import { Key, ShieldCheck, Save, Loader2, CreditCard } from "lucide-react";

export default function SettingsPage() {
  // 初始狀態 - 使用空字串確保 controlled input
  const [keys, setKeys] = useState({
    openai_key: "",
    llama_cloud_key: "",
  });

  // 獲取目前設定
  const { data: settings, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: settingsService.get,
  });

  // 當資料載入後，顯示配置狀態（不顯示實際 key）
  useEffect(() => {
    if (settings) {
      // Backend 只返回配置狀態，不返回實際 key
      // 保持 input 為空字串，用戶可以輸入新的 key
      // 如果已配置，顯示 placeholder 提示
    }
  }, [settings]);

  // 更新 Mutation
  const mutation = useMutation({
    mutationFn: settingsService.update,
    onSuccess: (data) => {
      // 更新本地狀態以反映最新值 (例如 masked keys)
      setKeys({
        openai_key: data.openai_key || "",
        llama_cloud_key: data.llama_cloud_key || "",
      });
      toast.success("Settings updated successfully.", {
        description: "Your API keys are now encrypted and stored.",
      });
    },
    onError: (err) => {
      toast.error("Failed to update settings.", {
        description: String(err),
      });
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setKeys((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
        <span className="text-muted-foreground">Loading settings...</span>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-20">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
          Tenant Settings
        </h2>
        <p className="text-muted-foreground">
          Manage global configurations and API keys for your organization.
        </p>
      </div>

      <div className="grid gap-6">
        {/* API Configuration Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Key className="h-5 w-5 text-primary" />
              <CardTitle>API Configuration</CardTitle>
            </div>
            <CardDescription>
              These keys power the AI capabilities across all your chatbots.
              They are stored securely using AES-256 encryption.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* OpenAI Key */}
            <div className="space-y-2">
              <label
                htmlFor="openai_key"
                className="text-sm font-medium leading-none">
                OpenAI API Key
              </label>
              <div className="relative">
                <Input
                  id="openai_key"
                  name="openai_key"
                  type="password"
                  value={keys.openai_key}
                  onChange={handleChange}
                  placeholder={
                    settings?.openai_key_configured
                      ? "••••••••••••••••••••••• (configured)"
                      : "sk-proj-..."
                  }
                  className="pr-10 font-mono"
                />
              </div>
              <p className="text-[0.8rem] text-muted-foreground flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 text-green-600" />
                Used for LLM generation (GPT-4o, GPT-3.5-turbo).
                {settings?.openai_key_configured && (
                  <span className="text-green-600 font-medium ml-1">
                    ✓ Configured
                  </span>
                )}
              </p>
            </div>

            <Separator />

            {/* LlamaCloud Key */}
            <div className="space-y-2">
              <label
                htmlFor="llama_cloud_key"
                className="text-sm font-medium leading-none">
                LlamaCloud API Key
              </label>
              <Input
                id="llama_cloud_key"
                name="llama_cloud_key"
                type="password"
                value={keys.llama_cloud_key}
                onChange={handleChange}
                placeholder={
                  settings?.llama_cloud_key_configured
                    ? "••••••••••••••••••••••• (configured)"
                    : "llx-..."
                }
                className="font-mono"
              />
              <p className="text-[0.8rem] text-muted-foreground flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 text-green-600" />
                Used for parsing complex documents (PDFs with tables) via
                LlamaParse.
                {settings?.llama_cloud_key_configured && (
                  <span className="text-green-600 font-medium ml-1">
                    ✓ Configured
                  </span>
                )}
              </p>
            </div>
          </CardContent>

          <CardFooter className="bg-muted/30 border-t flex justify-end py-4">
            <Button
              onClick={() => mutation.mutate(keys)}
              disabled={mutation.isPending}>
              {mutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              <Save className="mr-2 h-4 w-4" /> Save Changes
            </Button>
          </CardFooter>
        </Card>

        {/* Subscription / Usage (Placeholder for Future) */}
        <Card className="opacity-80">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-gray-500" />
              <CardTitle>Subscription & Usage</CardTitle>
            </div>
            <CardDescription>
              View your current plan usage and billing details.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-muted/50 border border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
              <p className="text-sm text-muted-foreground">
                Billing integration coming soon.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
