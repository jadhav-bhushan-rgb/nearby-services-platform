"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Admin } from "@/lib/types";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  admin: Admin | null;
  hydrated: boolean;
  setSession: (accessToken: string, refreshToken: string, admin: Admin) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setHydrated: () => void;
  clear: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      admin: null,
      hydrated: false,
      setSession: (accessToken, refreshToken, admin) => set({ accessToken, refreshToken, admin }),
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setHydrated: () => set({ hydrated: true }),
      clear: () => set({ accessToken: null, refreshToken: null, admin: null }),
    }),
    {
      name: "nearline-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        admin: state.admin,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    },
  ),
);
