"use client";

import Link from "next/link";
import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { CATEGORIES, categoryMeta, formatDistance } from "@/lib/categories";
import type { CategoryId } from "@/lib/types";

export default function DirectoryPage() {
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<CategoryId | "">("");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const query = useQuery({
    queryKey: ["directory", page, category, search],
    queryFn: () => api.listServices({ page, page_size: 10, category, q: search }),
    placeholderData: keepPreviousData,
  });
  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / query.data.page_size)) : 1;

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-5 py-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="font-serif text-3xl">Directory</p>
          <p className="text-sm text-neutral-600">Paged list of every published service.</p>
        </div>
        <Link className="text-sm underline" href="/">
          Map
        </Link>
      </div>
      <form
        className="mt-6 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setPage(1);
          setSearch(q.trim());
        }}
      >
        <input
          className="flex-1 rounded-lg border border-line bg-white px-3 py-2"
          placeholder="Search by name"
          value={q}
          onChange={(event) => setQ(event.target.value)}
        />
        <select
          className="rounded-lg border border-line bg-white px-3 py-2"
          value={category}
          onChange={(event) => {
            setCategory(event.target.value as CategoryId | "");
            setPage(1);
          }}
        >
          <option value="">All</option>
          {CATEGORIES.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
        <button className="rounded-lg bg-ink px-4 py-2 text-paper" type="submit">
          Search
        </button>
      </form>
      {query.isError ? <p className="mt-6 text-sm text-clay">The directory could not be loaded.</p> : null}
      <ul className="mt-6 divide-y divide-line rounded-2xl border border-line bg-card">
        {query.data?.items.map((service) => (
          <li key={service.id}>
            <Link className="flex items-center justify-between gap-4 px-4 py-3" href={`/services/${service.id}`}>
              <span>
                <span className="block font-medium">{service.name}</span>
                <span className="text-sm text-neutral-500">{categoryMeta(service.category).label}</span>
              </span>
              <span className="text-sm text-neutral-600">{formatDistance(service.distance_km) ?? service.rating?.toFixed(1) ?? ""}</span>
            </Link>
          </li>
        ))}
      </ul>
      {!query.isLoading && query.data?.items.length === 0 ? <p className="mt-4 text-sm">No services found.</p> : null}
      <div className="mt-4 flex items-center justify-between text-sm">
        <button className="underline disabled:opacity-40" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} type="button">
          Previous
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button
          className="underline disabled:opacity-40"
          disabled={page >= totalPages}
          onClick={() => setPage((value) => value + 1)}
          type="button"
        >
          Next
        </button>
      </div>
    </main>
  );
}
