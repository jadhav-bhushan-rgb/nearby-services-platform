"use client";

import Link from "next/link";
import { useState } from "react";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, api } from "@/lib/api";
import { CATEGORIES, categoryMeta } from "@/lib/categories";
import type { CategoryId } from "@/lib/types";

export default function ManageServicesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<CategoryId | "">("");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const query = useQuery({
    queryKey: ["admin-services", page, category, search],
    queryFn: () => api.adminServices({ page, page_size: 10, category, q: search }),
    placeholderData: keepPreviousData,
  });
  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / query.data.page_size)) : 1;

  return (
    <div>
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl">Services</h1>
          <p className="text-sm text-neutral-600">Update or remove a place. The public cache refreshes on save.</p>
        </div>
        <Link className="rounded-lg bg-moss px-3 py-2 text-sm text-white" href="/admin/services/new">
          Add service
        </Link>
      </div>
      <form
        className="mt-5 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setPage(1);
          setSearch(q.trim());
        }}
      >
        <input
          className="min-w-48 flex-1 rounded-lg border border-line bg-white px-3 py-2"
          placeholder="Search name"
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
          <option value="">All categories</option>
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
      {error ? <p className="mt-3 text-sm text-clay">{error}</p> : null}
      <div className="mt-4 overflow-x-auto rounded-2xl border border-line bg-card">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-line text-xs uppercase tracking-wide text-neutral-500">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="px-4 py-3 font-medium">Rating</th>
              <th className="px-4 py-3 font-medium">Location</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {query.data?.items.map((service) => (
              <tr key={service.id} className="border-b border-line last:border-0">
                <td className="px-4 py-3">{service.name}</td>
                <td className="px-4 py-3">{categoryMeta(service.category).label}</td>
                <td className="px-4 py-3">{service.rating?.toFixed(1) ?? "–"}</td>
                <td className="px-4 py-3 text-neutral-600">
                  {service.latitude.toFixed(4)}, {service.longitude.toFixed(4)}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link className="underline" href={`/admin/services/${service.id}`}>
                    Edit
                  </Link>
                  <button
                    className="ml-3 text-clay underline"
                    type="button"
                    onClick={async () => {
                      if (!window.confirm(`Delete ${service.name}?`)) return;
                      setError("");
                      try {
                        await api.deleteService(service.id);
                        await queryClient.invalidateQueries();
                      } catch (caught) {
                        setError(caught instanceof ApiError ? caught.message : "Delete failed");
                      }
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <button className="underline disabled:opacity-40" disabled={page <= 1} type="button" onClick={() => setPage((value) => value - 1)}>
          Previous
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button
          className="underline disabled:opacity-40"
          disabled={page >= totalPages}
          type="button"
          onClick={() => setPage((value) => value + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
