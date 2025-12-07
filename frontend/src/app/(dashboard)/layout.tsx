"use client";

import React, { useEffect } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Settings,
  LogOut,
  Brain,
  Sun,
  Moon,
} from "lucide-react";
import { useTheme } from "next-themes"; // 使用 next-themes 處理深色模式
import { Button } from "@/components/ui/button";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, logout, isLoading } = useAuth();
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();
  const router = useRouter();

  // 路由保護：未登入則踢回 login
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  // Loading 狀態顯示
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-slate-950">
        <div className="animate-pulse text-muted-foreground">
          Loading DocBrain...
        </div>
      </div>
    );
  }

  // 防止未登入閃爍內容
  if (!isAuthenticated) return null;

  const navItems = [
    { icon: LayoutDashboard, label: "Overview", path: "/" },
    { icon: Brain, label: "My Chatbots", path: "/chatbots" },
    { icon: Settings, label: "Settings", path: "/settings" },
  ];

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-slate-950 transition-colors duration-300">
      {/* Sidebar (Desktop) */}
      <aside className="w-64 bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800 hidden md:flex flex-col fixed h-full z-20">
        <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex items-center space-x-2">
          <div className="bg-primary text-primary-foreground p-1 rounded">
            <Brain size={24} />
          </div>
          <span className="text-xl font-bold text-gray-900 dark:text-white">
            DocBrain
          </span>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            // 判斷是否啟用：完全匹配 或 子路徑 (除了首頁)
            const isActive =
              pathname === item.path ||
              (item.path !== "/" && pathname.startsWith(item.path));

            return (
              <Link
                key={item.path}
                href={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-md transition-colors ${
                  isActive
                    ? "bg-blue-50 dark:bg-blue-900/20 text-primary font-medium"
                    : "text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-white"
                }`}>
                <item.icon size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-100 dark:border-slate-800 space-y-2 bg-white dark:bg-slate-900">
          <Button
            variant="ghost"
            className="w-full justify-start gap-3 text-gray-600 dark:text-slate-400"
            onClick={toggleTheme}>
            {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
            <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
          </Button>

          <Button
            variant="ghost"
            className="w-full justify-start gap-3 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
            onClick={logout}>
            <LogOut size={20} />
            <span>Sign Out</span>
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 md:ml-64 min-h-screen flex flex-col">
        {/* Mobile Header */}
        <header className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 px-6 py-4 md:hidden flex justify-between items-center sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <Brain size={24} className="text-primary" />
            <span className="text-lg font-bold dark:text-white">DocBrain</span>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="icon" onClick={toggleTheme}>
              {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
            </Button>
            <Button variant="ghost" size="icon" onClick={logout}>
              <LogOut size={20} />
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6 md:p-10 max-w-7xl mx-auto w-full flex-1">
          {children}
        </div>
      </main>
    </div>
  );
}
