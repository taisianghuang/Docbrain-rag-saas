"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { chatbotService } from "@/lib/api";

// UI Components
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Settings, Database, Play, Loader2 } from "lucide-react";

// Sub Components
import { ConfigTab } from "@/components/chatbot-detail/ConfigTab";
import { KnowledgeTab } from "@/components/chatbot-detail/KnowledgeTab";
import { PlaygroundTab } from "@/components/chatbot-detail/PlaygroundTab";

export default function ChatbotDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const {
    data: chatbot,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["chatbot", id],
    queryFn: async () => {
      const bots = await chatbotService.list();
      const bot = bots.find((b) => b.id === id);
      if (!bot) throw new Error("Chatbot not found");
      return bot;
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center space-x-2">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="text-muted-foreground">
          Loading chatbot configuration...
        </span>
      </div>
    );
  }

  if (error || !chatbot) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4">
        <div className="text-lg font-semibold">Chatbot not found</div>
        <Button onClick={() => router.push("/chatbots")}>Back to List</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => router.push("/chatbots")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white flex items-center gap-2">
              {chatbot.name}
              <Badge
                variant={chatbot.is_active ? "default" : "secondary"}
                className={
                  chatbot.is_active ? "bg-green-500 hover:bg-green-600" : ""
                }>
                {chatbot.is_active ? "Active" : "Inactive"}
              </Badge>
            </h1>
            <p className="text-sm text-muted-foreground font-mono">
              ID: {chatbot.public_id}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="configuration" className="space-y-4">
        <TabsList>
          <TabsTrigger value="configuration" className="flex gap-2">
            <Settings className="h-4 w-4" /> Configuration
          </TabsTrigger>
          <TabsTrigger value="knowledge" className="flex gap-2">
            <Database className="h-4 w-4" /> Knowledge Base
          </TabsTrigger>
          <TabsTrigger value="playground" className="flex gap-2">
            <Play className="h-4 w-4" /> Playground
          </TabsTrigger>
        </TabsList>

        <TabsContent
          value="configuration"
          className="space-y-4 animate-in fade-in-50 slide-in-from-bottom-2">
          <ConfigTab chatbot={chatbot} />
        </TabsContent>

        <TabsContent
          value="knowledge"
          className="space-y-4 animate-in fade-in-50 slide-in-from-bottom-2">
          <KnowledgeTab chatbotId={chatbot.id} ragConfig={chatbot.rag_config} />
        </TabsContent>

        <TabsContent
          value="playground"
          className="space-y-4 animate-in fade-in-50 slide-in-from-bottom-2">
          <PlaygroundTab chatbot={chatbot} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
