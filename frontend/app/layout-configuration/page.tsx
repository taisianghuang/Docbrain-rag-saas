"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import WidgetPreview from "@/components/WidgetPreview";
import { WidgetConfig } from "@/lib/types";

export default function LayoutConfigurationPage() {
  const [config, setConfig] = useState<WidgetConfig>({
    title: "Chat with DocBrain",
    primaryColor: "#2563eb",
    welcomeMessage: "Hi! Ask me anything about your documents.",
  });

  useEffect(() => {
    try {
      const stored = localStorage.getItem("widgetConfig");
      if (stored) setConfig(JSON.parse(stored));
    } catch (e) {}
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const name = e.target.name as keyof WidgetConfig;
    const value = e.target.value;
    setConfig((prev) => ({ ...prev, [name]: value }));
  };

  const save = () => {
    localStorage.setItem("widgetConfig", JSON.stringify(config));
    alert("Layout configuration saved");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Layout Configuration
        </h1>
        <p className="text-slate-500">
          Adjust the widget appearance and preview changes live.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Widget Appearance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Widget Title
                </label>
                <input
                  name="title"
                  value={config.title}
                  onChange={handleChange}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Primary Color
                </label>
                <div className="flex gap-2 items-center">
                  <input
                    type="color"
                    name="primaryColor"
                    value={config.primaryColor}
                    onChange={handleChange}
                    className="h-10 w-10 rounded cursor-pointer border-none p-0"
                  />
                  <input
                    type="text"
                    name="primaryColor"
                    value={config.primaryColor}
                    onChange={handleChange}
                    className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Welcome Message
                </label>
                <textarea
                  name="welcomeMessage"
                  rows={3}
                  value={config.welcomeMessage}
                  onChange={handleChange}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm resize-none"
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={save}>Save</Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Preview</CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ minHeight: 360 }}>
                <WidgetPreview config={config} />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
