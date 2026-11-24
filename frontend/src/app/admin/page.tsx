"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { categoryMeta } from "@/lib/categories";

export default function AdminHomePage() {
  const stats = useQuery({ queryKey: ["admin-stats"], queryFn: () => api.stats() });
  const recent = useQuery({
    queryKey: ["admin-recent"],
    queryFn: () => api.adminServices({ page: 1, page_size: 5 }),
  });

  return (
    <div>
      <h1 className="font-serif text-3xl">Overview</h1>
      <p className="mt-1 text-sm text-neutral-600">Published places currently on the public map.</p>
      {stats.isError ? <p className="mt-4 text-sm text-clay">Stats could not be loaded.</p> : null}
      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Stat label="Total" value={stats.data?.total} />
        {stats.data?.by_category.map((item) => (
          <Stat key={item.category} label={categoryMeta(item.category).label} value={item.count} />
        ))}
      </div>
      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-lg font-medium">Recently added</h2>
        <Link className="text-sm underline" href="/admin/services">
          Manage all
        </Link>
      </div>
      <ul className="mt-3 divide-y divide-line rounded-2xl border border-line bg-card">
        {recent.data?.items.map((service) => (
          <li key={service.id} className="flex items-center justify-between px-4 py-3 text-sm">
            <span>{service.name}</span>
            <span className="text-neutral-500">{categoryMeta(service.category).label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Stat({ label, value }: { label: string; value?: number }) {
  return (
    <div className="rounded-2xl border border-line bg-card px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-neutral-500">{label}</p>
      <p className="mt-1 text-2xl">{value ?? "–"}</p>
    </div>
  );
}
