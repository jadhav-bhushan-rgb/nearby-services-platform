"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError, api } from "@/lib/api";
import type { BulkResult } from "@/lib/types";

export default function UploadPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<BulkResult | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  return (
    <div className="max-w-2xl">
      <h1 className="font-serif text-3xl">Bulk upload</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Upload a CSV or JSON file with up to 1,000 services. CSV columns: name, category, latitude, longitude, rating,
        address, phone, description.
      </p>
      <form
        className="mt-6 space-y-4 rounded-2xl border border-line bg-card p-5"
        onSubmit={async (event) => {
          event.preventDefault();
          if (!file) return;
          setPending(true);
          setError("");
          setResult(null);
          try {
            const response = await api.bulkUpload(file);
            setResult(response);
            await queryClient.invalidateQueries();
          } catch (caught) {
            setError(caught instanceof ApiError ? caught.message : "Upload failed");
          } finally {
            setPending(false);
          }
        }}
      >
        <input
          type="file"
          accept=".csv,.json,application/json,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          required
        />
        <button className="rounded-lg bg-moss px-4 py-2 text-white disabled:opacity-60" disabled={pending} type="submit">
          {pending ? "Uploading" : "Upload"}
        </button>
      </form>
      {error ? <p className="mt-4 text-sm text-clay">{error}</p> : null}
      {result ? (
        <div className="mt-4 text-sm">
          <p>
            Created {result.created}. Failed {result.failed}.
          </p>
          <ul className="mt-2 space-y-1 text-clay">
            {result.errors.map((item, index) => (
              <li key={`${item.row}-${index}`}>
                Row {item.row ?? "?"}: {item.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
