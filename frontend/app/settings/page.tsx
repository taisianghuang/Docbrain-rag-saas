"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type ModelKeys = {
  openai?: string;
  gemini?: string;
  deepseed?: string;
};

export default function SettingsPage() {
  const [keys, setKeys] = useState<ModelKeys>({});

  useEffect(() => {
    try {
      const raw = localStorage.getItem("modelKeys");
      if (raw) setKeys(JSON.parse(raw));
    } catch (e) {}
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setKeys((prev) => ({ ...prev, [name]: value }));
  };

  const save = () => {
    localStorage.setItem("modelKeys", JSON.stringify(keys));
    alert("Model keys saved (stored in browser localStorage)");
  };

  return (
    <div>
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-slate-900">Model Keys</h1>
        <p className="text-slate-500">
          Configure API keys for different models.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  OpenAI Key
                </label>
                <input
                  name="openai"
                  value={keys.openai || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  placeholder="sk-..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Gemini Key
                </label>
                <input
                  name="gemini"
                  value={keys.gemini || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  placeholder="gemini-key..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  DeepSeed Key
                </label>
                <input
                  name="deepseed"
                  value={keys.deepseed || ""}
                  onChange={handleChange}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  placeholder="deepseed-key..."
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={save}>Save Keys</Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600">
                Keys are stored in your browser's localStorage for development.
                For production, use a secure server-side store and never expose
                secret keys in client code.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
