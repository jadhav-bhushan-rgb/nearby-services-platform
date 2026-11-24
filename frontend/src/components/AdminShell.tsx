"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const LINKS = [
  { href: "/admin", label: "Overview" },
  { href: "/admin/services", label: "Services" },
  { href: "/admin/services/new", label: "Add service" },
  { href: "/admin/upload", label: "Bulk upload" },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const hydrated = useAuthStore((state) => state.hydrated);
  const admin = useAuthStore((state) => state.admin);
  const token = useAuthStore((state) => state.accessToken);
  const setHydrated = useAuthStore((state) => state.setHydrated);
  const clear = useAuthStore((state) => state.clear);

  useEffect(() => {
    const timer = window.setTimeout(() => setHydrated(), 500);
    return () => window.clearTimeout(timer);
  }, [setHydrated]);

  useEffect(() => {
    if (hydrated && !token) router.replace("/admin/login");
  }, [hydrated, router, token]);

  if (!hydrated || !token) {
    return <div className="grid min-h-screen place-items-center text-sm text-neutral-500">Checking session</div>;
  }

  return (
    <div className="min-h-screen bg-paper text-ink lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="bg-ink px-5 py-6 text-paper">
        <Link href="/" className="font-serif text-2xl">
          Nearline
        </Link>
        <p className="mt-1 text-sm text-neutral-300">{admin?.full_name ?? "Admin"}</p>
        <nav className="mt-8 space-y-1">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`block rounded-lg px-3 py-2 text-sm ${active ? "bg-white/10" : "text-neutral-300"}`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <button
          className="mt-8 text-sm text-neutral-300 underline"
          type="button"
          onClick={async () => {
            try {
              await api.logout();
            } catch {
              // The local session is cleared either way.
            }
            clear();
            router.replace("/admin/login");
          }}
        >
          Log out
        </button>
      </aside>
      <div className="px-5 py-6 lg:px-8">{children}</div>
    </div>
  );
}
