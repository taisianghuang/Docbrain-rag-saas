"use client";

import { AxiosError } from "axios";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authService } from "@/lib/api";
import { SignupRequest } from "@/types";
import { toast } from "sonner";

// UI Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Brain, Loader2, ShieldCheck } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  // 表單狀態
  const [formData, setFormData] = useState<SignupRequest>({
    email: "",
    password: "",
    company_name: "",
    openai_key: "",
    llama_cloud_key: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await authService.register(formData);

      toast.success("Account created successfully!", {
        description: "Redirecting to login page...",
        duration: 2000,
      });

      // 延遲一下讓用戶看到成功訊息
      setTimeout(() => {
        router.push("/login");
      }, 1000);
    } catch (err) {
      console.error(err);
      let errorMessage = "Registration failed. Please try again.";

      // 3. 使用 instanceof 檢查是否為 Axios 錯誤
      if (err instanceof AxiosError && err.response?.data?.detail) {
        // 如果後端有回傳詳細錯誤 (FastAPI 的 detail 欄位)
        // 這裡需要斷言 data 是我們預期的結構，或者直接取用
        errorMessage = String(err.response.data.detail);
      } else if (err instanceof Error) {
        // 一般 JS 錯誤
        errorMessage = err.message;
      }
      toast.error("Registration Error", {
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950 px-4 py-12">
      <div className="w-full max-w-md space-y-8 bg-white dark:bg-slate-900 p-8 rounded-xl shadow-lg border border-gray-100 dark:border-slate-800">
        {/* Header Logo */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-primary text-primary-foreground rounded-lg flex items-center justify-center mb-4 shadow-md">
            <Brain size={28} />
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white">
            Create Account
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-slate-400">
            Start building smarter AI chatbots today.
          </p>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          {/* Basic Info Group */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1.5 block text-gray-700 dark:text-slate-300">
                Email Address <span className="text-red-500">*</span>
              </label>
              <Input
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="you@company.com"
                className="h-10"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1.5 block text-gray-700 dark:text-slate-300">
                Password <span className="text-red-500">*</span>
              </label>
              <Input
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="Min. 6 characters"
                minLength={6}
                className="h-10"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1.5 block text-gray-700 dark:text-slate-300">
                Company / Workspace Name
              </label>
              <Input
                name="company_name"
                value={formData.company_name}
                onChange={handleChange}
                placeholder="e.g. Acme Corp"
                className="h-10"
              />
            </div>
          </div>

          {/* API Keys Group (Optional) */}
          <div className="border-t border-gray-100 dark:border-slate-800 pt-5 mt-2">
            <div className="flex items-center mb-3">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                API Configuration (Optional)
              </h3>
              <span className="ml-2 px-2 py-0.5 rounded text-[10px] bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 font-medium">
                Secure Storage
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-slate-500 mb-4 leading-relaxed">
              Add your keys now to start using RAG features immediately, or
              configure them later in Settings.
            </p>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium mb-1.5 block text-gray-600 dark:text-slate-400 flex items-center">
                  OpenAI API Key
                </label>
                <Input
                  name="openai_key"
                  type="password"
                  value={formData.openai_key}
                  onChange={handleChange}
                  placeholder="sk-proj-..."
                  className="h-9 text-sm font-mono"
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1.5 block text-gray-600 dark:text-slate-400 flex items-center">
                  LlamaCloud Key (for Parsing)
                </label>
                <Input
                  name="llama_cloud_key"
                  type="password"
                  value={formData.llama_cloud_key}
                  onChange={handleChange}
                  placeholder="llx-..."
                  className="h-9 text-sm font-mono"
                />
              </div>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full h-11 mt-2 text-base shadow-md hover:shadow-lg transition-all"
            size="lg"
            disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Creating
                Account...
              </>
            ) : (
              "Create Account"
            )}
          </Button>
        </form>

        {/* Footer */}
        <div className="text-center text-sm">
          <span className="text-gray-500 dark:text-slate-400">
            Already have an account?{" "}
          </span>
          <Link
            href="/login"
            className="font-medium text-primary hover:text-blue-600 hover:underline transition-colors">
            Log in
          </Link>
        </div>
      </div>
    </div>
  );
}
