"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const [email, setEmail] = useState("admin@nearby.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  return (
    <main className="grid min-h-screen place-items-center bg-paper px-4">
      <form
        className="w-full max-w-md rounded-3xl border border-line bg-card p-8 shadow-panel"
        onSubmit={async (event) => {
          event.preventDefault();
          setPending(true);
          setError("");
          try {
            const tokens = await api.login(email, password);
            useAuthStore.getState().setTokens(tokens.access_token, tokens.refresh_token);
            const admin = await api.me();
            setSession(tokens.access_token, tokens.refresh_token, admin);
            router.replace("/admin");
          } catch (caught) {
            useAuthStore.getState().clear();
            setError(caught instanceof ApiError ? caught.message : "Login failed");
          } finally {
            setPending(false);
          }
        }}
      >
        <p className="font-serif text-3xl">Admin login</p>
        <p className="mt-1 text-sm text-neutral-600">Service edits stay behind this sign-in.</p>
        <label className="mt-6 block text-sm">
          Email
          <input
            className="mt-1 w-full rounded-lg border border-line bg-white px-3 py-2"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label className="mt-3 block text-sm">
          Password
          <input
            className="mt-1 w-full rounded-lg border border-line bg-white px-3 py-2"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            required
          />
        </label>
        {error ? <p className="mt-3 text-sm text-clay">{error}</p> : null}
        <button className="mt-5 w-full rounded-lg bg-ink py-2 text-paper disabled:opacity-60" disabled={pending} type="submit">
          {pending ? "Signing in" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
