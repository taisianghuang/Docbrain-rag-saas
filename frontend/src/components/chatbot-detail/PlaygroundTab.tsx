"use client";

import React, { useState, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { conversationService } from "@/lib/api";
import { Chatbot, ChatMessage, SourceNode } from "@/types";
import { toast } from "sonner";

// UI Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Bot,
  User,
  Send,
  Loader2,
  RefreshCw,
  Database,
  FileText,
} from "lucide-react";

interface PlaygroundTabProps {
  chatbot: Chatbot;
}

export function PlaygroundTab({ chatbot }: PlaygroundTabProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: chatbot.widget_config.welcome_message || "Hi! Ask me anything.",
    },
  ]);
  const [sources, setSources] = useState<SourceNode[]>([]);

  const chatMutation = useMutation({
    mutationFn: (newHistory: ChatMessage[]) =>
      conversationService.chat(chatbot.public_id, newHistory),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);
      setSources(data.source_nodes);
    },
    onError: () => {
      toast.error("Failed to get response from AI.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error connecting to the server.",
        },
      ]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return;

    const userMsg: ChatMessage = { role: "user", content: input };
    const newHistory = [...messages, userMsg];

    setMessages(newHistory);
    setInput("");
    chatMutation.mutate(newHistory);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
      {/* Chat Window */}
      <Card className="lg:col-span-2 flex flex-col h-full border-gray-200 dark:border-slate-800 shadow-sm">
        <CardHeader className="py-3 px-4 border-b bg-muted/20">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" />
              Preview: {chatbot.name}
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setMessages([
                  {
                    role: "assistant",
                    content: chatbot.widget_config.welcome_message || "Hi!",
                  },
                ]);
                setSources([]);
                toast.info("Conversation reset.");
              }}>
              <RefreshCw className="h-4 w-4 text-muted-foreground" />
            </Button>
          </div>
        </CardHeader>

        <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`flex max-w-[85%] gap-2 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                <div
                  className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}>
                  {msg.role === "user" ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>
                <div
                  className={`p-3 rounded-lg text-sm whitespace-pre-wrap leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-background border"
                  }`}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          {chatMutation.isPending && (
            <div className="flex justify-start">
              <div className="flex max-w-[80%] gap-2 flex-row">
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="bg-background border p-3 rounded-lg text-sm flex items-center text-muted-foreground">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Thinking...
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t bg-background rounded-b-xl">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question..."
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={chatMutation.isPending}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={chatMutation.isPending || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Retrieval Context */}
      <Card className="h-full flex flex-col border-gray-200 dark:border-slate-800 shadow-sm">
        <CardHeader className="py-3 px-4 border-b bg-muted/20">
          <CardTitle className="text-base flex items-center gap-2">
            <Database className="h-4 w-4 text-blue-500" />
            Retrieval Context
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-3">
          {sources.length > 0 ? (
            sources.map((source, i) => (
              <div
                key={i}
                className="text-xs border rounded-md p-3 bg-muted/10 hover:bg-muted/20 transition-colors">
                <div className="flex justify-between mb-2 text-muted-foreground font-medium">
                  <span
                    className="truncate max-w-[120px]"
                    title={source.metadata?.filename}>
                    {source.metadata?.filename || "Unknown Doc"}
                  </span>
                  <Badge
                    variant="outline"
                    className="text-[10px] h-5 px-1 font-normal">
                    Score: {(source.score * 100).toFixed(0)}%
                  </Badge>
                </div>
                <p className="text-foreground/80 italic line-clamp-4 leading-relaxed border-l-2 border-primary/20 pl-2">
                  &quot;{source.text}&quot;
                </p>
              </div>
            ))
          ) : (
            <div className="text-center text-muted-foreground py-10 flex flex-col items-center">
              <FileText className="h-10 w-10 opacity-20 mb-2" />
              <p className="text-sm font-medium">No citations available.</p>
              <p className="text-xs opacity-70 mt-1 max-w-[150px]">
                Ask a question to see which document chunks are retrieved.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
