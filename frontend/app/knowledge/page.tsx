"use client";
import React, { useState, useCallback } from "react";
import {
  UploadCloud,
  File as FileIcon,
  Trash2,
  CheckCircle,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Doc = {
  id: string;
  name: string;
  size: string;
  status: "ready" | "indexing" | "error";
  uploadedAt: string;
};

const MOCK_DOCUMENTS: Doc[] = [
  {
    id: "a1",
    name: "Q1_Report.pdf",
    size: "1.2 MB",
    status: "ready",
    uploadedAt: "1 day ago",
  },
  {
    id: "b2",
    name: "Terms.txt",
    size: "12 KB",
    status: "indexing",
    uploadedAt: "2 hours ago",
  },
];

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Doc[]>(MOCK_DOCUMENTS);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      simulateUpload(files[0]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      simulateUpload(e.target.files[0]);
    }
  };

  const simulateUpload = (file: File) => {
    setUploading(true);
    setTimeout(() => {
      const newDoc: Doc = {
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: formatSize(file.size),
        status: "ready",
        uploadedAt: "Just now",
      };
      setDocuments((prev) => [newDoc, ...prev]);
      setUploading(false);
    }, 1500);
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const handleDelete = (id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  return (
    <div>
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-slate-900">Knowledge Base</h1>
        <p className="text-slate-500">
          Manage the documents that power your AI chatbot.
        </p>
      </header>

      <Card
        className={`border-2 border-dashed transition-colors ${
          isDragging ? "border-blue-500 bg-blue-50" : "border-slate-200"
        }`}>
        <CardContent
          className="p-12 flex flex-col items-center justify-center text-center"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}>
          <div className="bg-slate-100 p-4 rounded-full mb-4">
            {uploading ? (
              <Loader2 className="animate-spin text-blue-600" size={32} />
            ) : (
              <UploadCloud className="text-slate-400" size={32} />
            )}
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            {uploading ? "Processing Document..." : "Upload Documents"}
          </h3>
          <p className="text-slate-500 mb-6 max-w-sm">
            Drag and drop PDF, TXT, or MD files here to ingest them into the
            vector database.
          </p>
          <div className="relative">
            <input
              type="file"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleFileInput}
              accept=".pdf,.txt,.md"
              disabled={uploading}
            />
            <Button disabled={uploading}>Select Files</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Indexed Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="py-4 flex items-center justify-between hover:bg-slate-50 transition-colors rounded-lg px-2 -mx-2">
                <div className="flex items-center gap-4">
                  <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                    <FileIcon size={20} />
                  </div>
                  <div>
                    <h4 className="font-medium text-slate-900">{doc.name}</h4>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span>{doc.size}</span>
                      <span>•</span>
                      <span>{doc.uploadedAt}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div
                    className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      doc.status === "ready"
                        ? "bg-green-100 text-green-700"
                        : doc.status === "indexing"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                    {doc.status === "ready" ? (
                      <CheckCircle size={12} />
                    ) : doc.status === "indexing" ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <AlertCircle size={12} />
                    )}
                    {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                  </div>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-slate-400 hover:text-red-500 transition-colors p-2">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}

            {documents.length === 0 && (
              <div className="py-8 text-center text-slate-500">
                No documents uploaded yet.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
