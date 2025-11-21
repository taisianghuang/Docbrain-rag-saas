"use client";
import React, { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send } from "lucide-react";
import { WidgetConfig, ChatMessage } from "@/lib/types";
import { chatWithBackend } from "@/lib/services";

interface WidgetPreviewProps {
  config: WidgetConfig;
}

export default function WidgetPreview({ config }: WidgetPreviewProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "model", text: config.welcomeMessage, timestamp: Date.now() },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Reset welcome message when config changes
    setMessages((prev) => {
      const userMessages = prev.filter((m) => m.timestamp !== 0);
      return [
        { role: "model", text: config.welcomeMessage, timestamp: 0 },
        ...userMessages,
      ];
    });
  }, [config.welcomeMessage]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen, isLoading]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMsg: ChatMessage = {
      role: "user",
      text: inputValue,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    const responseTimestamp = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      { role: "model", text: "", timestamp: responseTimestamp },
    ]);

    try {
      const history = messages.filter((m) => m.timestamp !== responseTimestamp);
      await chatWithBackend(userMsg.text, [...history, userMsg], (chunk) => {
        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.timestamp === responseTimestamp) {
              return { ...msg, text: msg.text + chunk };
            }
            return msg;
          })
        );
        setIsLoading(false);
      });
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.timestamp === responseTimestamp
            ? {
                ...msg,
                text: "Sorry, something went wrong connecting to the server.",
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end font-sans">
      {isOpen && (
        <div className="mb-4 w-[350px] rounded-lg bg-white shadow-2xl ring-1 ring-black/5 overflow-hidden flex flex-col transition-all duration-200 ease-in-out h-[500px]">
          <div
            className="flex items-center justify-between p-4 text-white"
            style={{ backgroundColor: config.primaryColor }}>
            <h3 className="font-semibold text-sm">{config.title}</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-white/20 p-1 rounded">
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 bg-slate-50 space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm shadow-sm whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-slate-800 text-white rounded-br-none"
                      : "bg-white text-slate-800 border border-slate-200 rounded-bl-none"
                  }`}
                  style={
                    msg.role === "user"
                      ? { backgroundColor: config.primaryColor }
                      : {}
                  }>
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-3 bg-white border-t border-slate-100">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Ask a question..."
                className="flex-1 text-sm outline-none text-slate-700 placeholder:text-slate-400"
              />
              <button
                onClick={handleSendMessage}
                disabled={
                  isLoading && messages[messages.length - 1]?.text === ""
                }
                className="p-2 rounded-full hover:bg-slate-100 text-blue-600 disabled:opacity-50 transition-colors"
                style={{ color: config.primaryColor }}>
                <Send size={18} />
              </button>
            </div>
            <div className="text-[10px] text-center text-slate-400 mt-2">
              Powered by DocBrain AI
            </div>
          </div>
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-center w-14 h-14 rounded-full shadow-lg transition-transform hover:scale-105 text-white"
        style={{ backgroundColor: config.primaryColor }}>
        {isOpen ? <X size={24} /> : <MessageCircle size={28} />}
      </button>
    </div>
  );
}
