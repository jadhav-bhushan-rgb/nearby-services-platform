"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { CATEGORIES, CITY_CENTER } from "@/lib/categories";
import type { CategoryId, Service, ServiceInput } from "@/lib/types";

const ServiceMap = dynamic(() => import("@/components/ServiceMap"), { ssr: false });

type Props = {
  initial?: Service;
  pending?: boolean;
  error?: string;
  submitLabel: string;
  onSubmit: (body: ServiceInput) => void;
};

export function ServiceForm({ initial, pending, error, submitLabel, onSubmit }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [category, setCategory] = useState<CategoryId>(initial?.category ?? "hospital");
  const [latitude, setLatitude] = useState(initial?.latitude ?? CITY_CENTER.latitude);
  const [longitude, setLongitude] = useState(initial?.longitude ?? CITY_CENTER.longitude);
  const [rating, setRating] = useState(initial?.rating?.toString() ?? "");
  const [address, setAddress] = useState(stringMeta(initial, "address"));
  const [phone, setPhone] = useState(stringMeta(initial, "phone"));
  const [description, setDescription] = useState(stringMeta(initial, "description"));

  const marker = useMemo<Service[]>(
    () => [
      {
        id: initial?.id ?? "draft",
        name: name || "New service",
        category,
        latitude: Number(latitude) || CITY_CENTER.latitude,
        longitude: Number(longitude) || CITY_CENTER.longitude,
        rating: rating ? Number(rating) : null,
        metadata: null,
        created_at: "",
        updated_at: "",
      },
    ],
    [category, initial?.id, latitude, longitude, name, rating],
  );

  return (
    <form
      className="grid gap-6 lg:grid-cols-[420px_1fr]"
      onSubmit={(event) => {
        event.preventDefault();
        const metadata = {
          ...(address ? { address } : {}),
          ...(phone ? { phone } : {}),
          ...(description ? { description } : {}),
        };
        onSubmit({
          name,
          category,
          latitude: Number(latitude),
          longitude: Number(longitude),
          rating: rating === "" ? null : Number(rating),
          clear_rating: rating === "",
          metadata,
        });
      }}
    >
      <div className="space-y-3">
        <Field label="Name">
          <input className={fieldClass} value={name} onChange={(event) => setName(event.target.value)} required maxLength={200} />
        </Field>
        <Field label="Category">
          <select className={fieldClass} value={category} onChange={(event) => setCategory(event.target.value as CategoryId)}>
            {CATEGORIES.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Latitude">
            <input className={fieldClass} type="number" step="0.000001" value={latitude} onChange={(event) => setLatitude(Number(event.target.value))} required />
          </Field>
          <Field label="Longitude">
            <input className={fieldClass} type="number" step="0.000001" value={longitude} onChange={(event) => setLongitude(Number(event.target.value))} required />
          </Field>
        </div>
        <Field label="Rating (optional)">
          <input className={fieldClass} type="number" min="0" max="5" step="0.1" value={rating} onChange={(event) => setRating(event.target.value)} />
        </Field>
        <Field label="Address">
          <input className={fieldClass} value={address} onChange={(event) => setAddress(event.target.value)} />
        </Field>
        <Field label="Phone">
          <input className={fieldClass} value={phone} onChange={(event) => setPhone(event.target.value)} />
        </Field>
        <Field label="Description">
          <textarea className={`${fieldClass} min-h-24`} value={description} onChange={(event) => setDescription(event.target.value)} />
        </Field>
        {error ? <p className="text-sm text-clay">{error}</p> : null}
        <button className="rounded-lg bg-moss px-4 py-2 text-white disabled:opacity-60" disabled={pending} type="submit">
          {pending ? "Saving" : submitLabel}
        </button>
        <p className="text-xs text-neutral-500">Click the map to set the location.</p>
      </div>
      <div className="h-[420px] overflow-hidden rounded-2xl border border-line">
        <ServiceMap
          markers={marker}
          center={[Number(latitude) || CITY_CENTER.latitude, Number(longitude) || CITY_CENTER.longitude]}
          zoom={14}
          selectedId={marker[0].id}
          onPick={(lat, lng) => {
            setLatitude(Number(lat.toFixed(6)));
            setLongitude(Number(lng.toFixed(6)));
          }}
        />
      </div>
    </form>
  );
}

function stringMeta(service: Service | undefined, key: string) {
  const value = service?.metadata?.[key];
  return typeof value === "string" ? value : "";
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-neutral-600">{label}</span>
      {children}
    </label>
  );
}

const fieldClass = "w-full rounded-lg border border-line bg-white px-3 py-2";
