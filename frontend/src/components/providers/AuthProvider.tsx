"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { authService } from "@/lib/api";
import { useRouter } from "next/navigation"; // 注意：用 next/navigation

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (formData: FormData) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true); // 預設 true 以避免畫面閃爍
  const router = useRouter();

  useEffect(() => {
    const storedToken = localStorage.getItem("docbrain_token");
    if (storedToken) {
      setToken(storedToken);
    }
    setIsLoading(false);
  }, []);

  const login = async (formData: FormData) => {
    setIsLoading(true);
    try {
      const data = await authService.login(formData);
      setToken(data.access_token);
      localStorage.setItem("docbrain_token", data.access_token);
      router.push("/"); // 登入後跳轉首頁
    } catch (error) {
      console.error("Login failed", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem("docbrain_token");
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated: !!token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
