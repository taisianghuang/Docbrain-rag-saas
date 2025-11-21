"use client";
import Link from "next/link";
import { Home, FileText, Settings, Layout } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Sidebar() {
  return (
    <aside className="h-screen w-64 border-r bg-white">
      <div className="flex h-16 items-center px-4">
        <h2 className="text-lg font-semibold">DocBrain</h2>
      </div>

      <nav className="mt-4 flex flex-col gap-1 px-2">
        <Link href="/" className="no-underline">
          <Button variant="ghost" className="w-full justify-start">
            <Home className="mr-2" /> Dashboard
          </Button>
        </Link>

        <Link href="/knowledge" className="no-underline">
          <Button variant="ghost" className="w-full justify-start">
            <FileText className="mr-2" /> Knowledge
          </Button>
        </Link>

        <Link href="/layout-configuration" className="no-underline">
          <Button variant="ghost" className="w-full justify-start">
            <Layout className="mr-2" /> Layout
          </Button>
        </Link>

        <Link href="/settings" className="no-underline">
          <Button variant="ghost" className="w-full justify-start">
            <Settings className="mr-2" /> Model Keys
          </Button>
        </Link>
      </nav>
    </aside>
  );
}
