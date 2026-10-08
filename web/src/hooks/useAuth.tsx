"use client";

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/services/api";
import type { ProfileUpdatePayload, User } from "@/services/types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  signup: (payload: {
    username: string;
    email: string;
    password: string;
    password2: string;
  }) => Promise<void>;
  login: (payload: { username: string; password: string }) => Promise<void>;
  continueAsGuest: () => Promise<void>;
  updateProfile: (payload: ProfileUpdatePayload) => Promise<void>;
  deleteAccount: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = "lingolab_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const stored = window.localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setIsLoading(false);
      return;
    }
    setToken(stored);
    api
      .me()
      .then(setUser)
      .catch(() => {
        window.localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const applyAuth = useCallback((nextUser: User, nextToken: string) => {
    window.localStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
    setUser(nextUser);
  }, []);

  const signup = useCallback(
    async (payload: { username: string; email: string; password: string; password2: string }) => {
      const res = await api.signup(payload);
      applyAuth(res.user, res.token);
    },
    [applyAuth]
  );

  const login = useCallback(
    async (payload: { username: string; password: string }) => {
      const res = await api.login(payload);
      applyAuth(res.user, res.token);
    },
    [applyAuth]
  );

  const continueAsGuest = useCallback(async () => {
    const res = await api.guest();
    applyAuth(res.user, res.token);
  }, [applyAuth]);

  const updateProfile = useCallback(async (payload: ProfileUpdatePayload) => {
    const nextUser = await api.updateProfile(payload);
    setUser(nextUser);
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  const deleteAccount = useCallback(async () => {
    await api.deleteAccount();
    window.localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    router.push("/");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        signup,
        login,
        continueAsGuest,
        updateProfile,
        deleteAccount,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

export { ApiError };
