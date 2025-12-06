"use client";

import React, { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentService } from "@/lib/api";
import { RagConfig } from "@/types";
import { toast } from "sonner";

// UI Components
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Upload, FileText, Trash2, Loader2 } from "lucide-react";

interface KnowledgeTabProps {
  chatbotId: string;
  ragConfig: RagConfig;
}

export function KnowledgeTab({ chatbotId, ragConfig }: KnowledgeTabProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents", chatbotId],
    queryFn: () => documentService.list(chatbotId),
  });

  const ingestMutation = useMutation({
    mutationFn: (file: File) => documentService.ingest(file, chatbotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", chatbotId] });
      toast.success("File uploaded successfully.", {
        description: "Processing has started.",
      });
    },
    onError: (err) => toast.error("Upload failed: " + err),
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => documentService.delete(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", chatbotId] });
      toast.success("Document deleted.");
    },
    onError: (err) => toast.error("Delete failed: " + err),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];

      const isFirstUpload = !documents || documents.length === 0;

      if (isFirstUpload) {
        const confirmed = confirm(
          `Important: Uploading "${file.name}" will lock your configuration.\n\n` +
            `Current Settings:\n` +
            `- Strategy: ${ragConfig.chunking_strategy}\n` +
            `- Mode: ${ragConfig.mode}\n\n` +
            `Do you want to proceed?`
        );
        if (confirmed) {
          ingestMutation.mutate(file);
        }
      } else {
        ingestMutation.mutate(file);
      }
      e.target.value = "";
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card
        className="border-dashed border-2 hover:border-primary/50 hover:bg-muted/5 transition-all cursor-pointer group"
        onClick={() => fileInputRef.current?.click()}>
        <CardContent className="flex flex-col items-center justify-center py-10 text-center">
          <div className="p-4 bg-primary/10 rounded-full mb-4 group-hover:scale-110 transition-transform duration-200">
            <Upload className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold">Upload Knowledge</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Drag and drop or click to upload PDF, DOCX, TXT, MD
          </p>
          <Button disabled={ingestMutation.isPending} variant="secondary">
            {ingestMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            {ingestMutation.isPending ? "Processing..." : "Select File"}
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileChange}
          />
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle>Indexed Documents ({documents?.length || 0})</CardTitle>
          <CardDescription>
            Documents currently serving as context for your AI.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {isLoading && (
              <div className="text-center py-4 text-muted-foreground animate-pulse">
                Loading documents...
              </div>
            )}

            {documents?.length === 0 && !isLoading && (
              <div className="text-center py-8 text-muted-foreground">
                No documents uploaded yet.
              </div>
            )}

            {documents?.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-blue-600 flex-shrink-0">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{doc.name}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>
                        {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                      <span>•</span>
                      <Badge
                        variant="outline"
                        className={`
                        text-[10px] px-1 py-0 h-5 font-normal border-0
                        ${doc.status === "indexed" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : ""}
                        ${doc.status === "processing" ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" : ""}
                        ${doc.status === "error" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" : ""}
                      `}>
                        {doc.status}
                      </Badge>
                    </div>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive"
                  disabled={deleteMutation.isPending}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (
                      confirm(
                        "Are you sure you want to delete this document? It cannot be undone."
                      )
                    ) {
                      deleteMutation.mutate(doc.id);
                    }
                  }}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
