"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { CATEGORIES, CITY_CENTER, categoryMeta, formatDistance } from "@/lib/categories";
import type { Bounds, CategoryId, Service } from "@/lib/types";

const ServiceMap = dynamic(() => import("@/components/ServiceMap"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-[#e7e1d6]" />,
});

const RADII = [1, 2, 5, 10, 25];

export function MapExplorer() {
  const [category, setCategory] = useState<CategoryId | "">("");
  const [bounds, setBounds] = useState<Bounds | null>(null);
  const [mode, setMode] = useState<"browse" | "nearby">("browse");
  const [origin, setOrigin] = useState(CITY_CENTER);
  const [draft, setDraft] = useState(CITY_CENTER);
  const [radius, setRadius] = useState(5);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [geoError, setGeoError] = useState("");

  const mapQuery = useQuery({
    queryKey: ["map", bounds, category],
    queryFn: () => api.mapServices({ ...bounds!, category, limit: 300 }),
    enabled: mode === "browse" && bounds !== null,
    placeholderData: keepPreviousData,
  });
  const nearbyQuery = useQuery({
    queryKey: ["nearby", origin, radius, category],
    queryFn: () =>
      api.nearby({
        latitude: origin.latitude,
        longitude: origin.longitude,
        radius_km: radius,
        category,
        limit: 100,
      }),
    enabled: mode === "nearby",
  });

  const active = mode === "nearby" ? nearbyQuery : mapQuery;
  const services = active.data?.items ?? [];
  const selected = services.find((item) => item.id === selectedId) ?? null;
  const fitSignature = useMemo(() => {
    if (mode !== "nearby") return undefined;
    return services.map((item) => item.id).join("|");
  }, [mode, services]);

  function searchNearby(next = draft) {
    setOrigin(next);
    setDraft(next);
    setMode("nearby");
    sessionStorage.setItem("nearline-origin", JSON.stringify(next));
  }

  function useMyLocation() {
    setGeoError("");
    if (!navigator.geolocation) {
      setGeoError("This browser does not share location.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        searchNearby({ latitude: position.coords.latitude, longitude: position.coords.longitude });
      },
      () => setGeoError("Location permission was denied. Enter coordinates instead."),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  return (
    <div className="grid h-[100dvh] grid-rows-[minmax(280px,52vh)_1fr] bg-paper text-ink lg:grid-cols-[400px_1fr] lg:grid-rows-1">
      <section className="relative order-1 min-h-0 lg:order-2">
        <ServiceMap
          markers={services}
          center={[origin.latitude, origin.longitude]}
          selectedId={selectedId}
          userLocation={mode === "nearby" ? [origin.latitude, origin.longitude] : null}
          radiusKm={mode === "nearby" ? radius : null}
          fitSignature={fitSignature}
          onBounds={mode === "browse" ? setBounds : undefined}
          onSelect={setSelectedId}
        />
        <div className="pointer-events-none absolute right-4 top-4 hidden rounded-full bg-card/95 px-3 py-1 text-xs shadow-panel lg:block">
          Bengaluru sample area
        </div>
      </section>

      <aside className="order-2 flex min-h-0 flex-col border-line bg-card lg:order-1 lg:border-r">
        <div className="border-b border-line px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-serif text-2xl tracking-tight">Nearline</p>
              <p className="text-sm text-neutral-600">Hospitals, ATMs, shops, and everyday places.</p>
            </div>
            <div className="flex gap-3 text-sm">
              <Link className="underline" href="/directory">
                Directory
              </Link>
              <Link className="underline" href="/admin">
                Admin
              </Link>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <FilterChip active={category === ""} onClick={() => setCategory("")}>
              All
            </FilterChip>
            {CATEGORIES.map((item) => (
              <FilterChip key={item.id} active={category === item.id} onClick={() => setCategory(item.id)}>
                <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: item.color }} />
                {item.label}
              </FilterChip>
            ))}
          </div>
        </div>

        <form
          className="grid grid-cols-2 gap-2 border-b border-line px-5 py-4"
          onSubmit={(event) => {
            event.preventDefault();
            searchNearby();
          }}
        >
          <label className="text-xs text-neutral-600">
            Latitude
            <input
              className="mt-1 w-full rounded-lg border border-line bg-paper px-2 py-1.5"
              value={draft.latitude}
              onChange={(event) => setDraft({ ...draft, latitude: Number(event.target.value) })}
              type="number"
              step="0.0001"
              required
            />
          </label>
          <label className="text-xs text-neutral-600">
            Longitude
            <input
              className="mt-1 w-full rounded-lg border border-line bg-paper px-2 py-1.5"
              value={draft.longitude}
              onChange={(event) => setDraft({ ...draft, longitude: Number(event.target.value) })}
              type="number"
              step="0.0001"
              required
            />
          </label>
          <label className="col-span-2 text-xs text-neutral-600">
            Radius
            <select
              className="mt-1 w-full rounded-lg border border-line bg-paper px-2 py-1.5"
              value={radius}
              onChange={(event) => setRadius(Number(event.target.value))}
            >
              {RADII.map((value) => (
                <option key={value} value={value}>
                  {value} km
                </option>
              ))}
            </select>
          </label>
          <button className="rounded-lg bg-moss px-3 py-2 text-sm text-white" type="submit">
            Search nearby
          </button>
          <button className="rounded-lg border border-line px-3 py-2 text-sm" type="button" onClick={useMyLocation}>
            Use my location
          </button>
          {mode === "nearby" ? (
            <button
              className="col-span-2 text-left text-sm underline"
              type="button"
              onClick={() => setMode("browse")}
            >
              Back to the map view
            </button>
          ) : null}
          {geoError ? <p className="col-span-2 text-sm text-clay">{geoError}</p> : null}
        </form>

        <div className="min-h-0 flex-1 overflow-auto px-3 py-3">
          <div className="mb-2 flex items-center justify-between px-2 text-xs uppercase tracking-wide text-neutral-500">
            <span>{mode === "nearby" ? `Within ${radius} km` : "In view"}</span>
            <span>{active.isFetching ? "Updating" : `${services.length} places`}</span>
          </div>
          {active.isError ? <p className="px-2 text-sm text-clay">The service list could not be loaded.</p> : null}
          {mode === "browse" && mapQuery.data?.truncated ? (
            <p className="px-2 pb-2 text-sm text-neutral-600">Zoom in to see every place in this area.</p>
          ) : null}
          <ul className="space-y-1">
            {services.map((service) => (
              <li key={service.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(service.id)}
                  className={`w-full rounded-xl px-3 py-2 text-left ${selectedId === service.id ? "bg-paper" : "hover:bg-paper/70"}`}
                >
                  <ServiceRow service={service} />
                </button>
              </li>
            ))}
          </ul>
          {!active.isLoading && services.length === 0 ? (
            <p className="px-2 pt-4 text-sm text-neutral-600">No places match this view.</p>
          ) : null}
          {selected ? (
            <Link className="mt-3 block px-2 text-sm font-medium text-moss underline" href={`/services/${selected.id}`}>
              Open {selected.name}
            </Link>
          ) : null}
        </div>
      </aside>
    </div>
  );
}

function FilterChip({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-sm ${active ? "border-ink bg-ink text-paper" : "border-line bg-paper"}`}
    >
      {children}
    </button>
  );
}

function ServiceRow({ service }: { service: Service }) {
  const meta = categoryMeta(service.category);
  const distance = formatDistance(service.distance_km);
  return (
    <span className="flex items-start justify-between gap-3">
      <span>
        <span className="block text-sm font-medium">{service.name}</span>
        <span className="text-xs text-neutral-500">{meta.label}</span>
      </span>
      <span className="text-right text-xs text-neutral-600">
        {service.rating != null ? <span className="block">{service.rating.toFixed(1)}</span> : null}
        {distance ? <span className="block">{distance}</span> : null}
      </span>
    </span>
  );
}
