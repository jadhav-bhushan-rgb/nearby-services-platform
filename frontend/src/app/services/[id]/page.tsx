"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { categoryMeta, formatDistance } from "@/lib/categories";

const ServiceMap = dynamic(() => import("@/components/ServiceMap"), { ssr: false });

export default function ServiceDetailPage() {
  const params = useParams<{ id: string }>();
  const [origin, setOrigin] = useState<{ latitude: number; longitude: number } | undefined>();

  useEffect(() => {
    const saved = sessionStorage.getItem("nearline-origin");
    if (!saved) return;
    try {
      setOrigin(JSON.parse(saved));
    } catch {
      sessionStorage.removeItem("nearline-origin");
    }
  }, []);

  const query = useQuery({
    queryKey: ["service", params.id, origin],
    queryFn: () => api.service(params.id, origin),
  });
  const service = query.data;

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-5 py-8">
      <Link className="text-sm underline" href="/">
        Back to map
      </Link>
      {query.isLoading ? <p className="mt-8 text-sm">Loading place</p> : null}
      {query.isError ? <p className="mt-8 text-sm text-clay">This place is unavailable.</p> : null}
      {service ? (
        <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <p className="text-xs uppercase tracking-wide text-neutral-500">{categoryMeta(service.category).label}</p>
            <h1 className="mt-1 font-serif text-4xl">{service.name}</h1>
            <dl className="mt-6 space-y-3 text-sm">
              {service.rating != null ? <Row label="Rating" value={service.rating.toFixed(1)} /> : null}
              {formatDistance(service.distance_km) ? <Row label="Distance" value={formatDistance(service.distance_km) ?? ""} /> : null}
              {textMeta(service.metadata?.address) ? <Row label="Address" value={textMeta(service.metadata?.address)} /> : null}
              {textMeta(service.metadata?.phone) ? <Row label="Phone" value={textMeta(service.metadata?.phone)} /> : null}
              {textMeta(service.metadata?.description) ? <Row label="About" value={textMeta(service.metadata?.description)} /> : null}
              <Row label="Added" value={new Date(service.created_at).toLocaleString()} />
            </dl>
          </div>
          <div className="h-[420px] overflow-hidden rounded-2xl border border-line">
            <ServiceMap
              markers={[service]}
              center={[service.latitude, service.longitude]}
              zoom={15}
              selectedId={service.id}
            />
          </div>
        </div>
      ) : null}
    </main>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-neutral-500">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function textMeta(value: unknown) {
  return typeof value === "string" ? value : "";
}
