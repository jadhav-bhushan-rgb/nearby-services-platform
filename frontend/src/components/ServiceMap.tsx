"use client";

import { useEffect, useMemo } from "react";
import { Circle, CircleMarker, MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { categoryMeta, formatDistance } from "@/lib/categories";
import type { Bounds, Service } from "@/lib/types";

type Props = {
  markers: Service[];
  center: [number, number];
  zoom?: number;
  selectedId?: string | null;
  userLocation?: [number, number] | null;
  radiusKm?: number | null;
  fitSignature?: string;
  onBounds?: (bounds: Bounds) => void;
  onSelect?: (id: string) => void;
  onPick?: (latitude: number, longitude: number) => void;
};

function iconFor(category: string, selected: boolean) {
  const color = categoryMeta(category).color;
  const size = selected ? 22 : 16;
  return L.divIcon({
    className: "service-pin",
    html: `<span style="width:${size}px;height:${size}px;background:${color};outline:${selected ? "3px solid #1c1915" : "none"}"></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function BoundsReporter({ onBounds }: { onBounds?: (bounds: Bounds) => void }) {
  const map = useMapEvents({
    moveend() {
      publish(map);
    },
  });
  useEffect(() => {
    publish(map);
  }, [map, onBounds]);
  return null;

  function publish(current: L.Map) {
    if (!onBounds) return;
    const box = current.getBounds();
    onBounds({
      min_lat: box.getSouth(),
      min_lng: box.getWest(),
      max_lat: box.getNorth(),
      max_lng: box.getEast(),
    });
  }
}

function FitTo({ signature, points }: { signature?: string; points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (!signature || points.length === 0) return;
    map.fitBounds(L.latLngBounds(points).pad(0.25), { maxZoom: 15 });
  }, [signature, map]);
  return null;
}

function FlyToSelected({ position }: { position: [number, number] | null }) {
  const map = useMap();
  const key = position ? `${position[0]},${position[1]}` : "";
  useEffect(() => {
    if (!key) return;
    const [latitude, longitude] = key.split(",").map(Number);
    map.flyTo([latitude, longitude], Math.max(map.getZoom(), 15), { duration: 0.6 });
  }, [key, map]);
  return null;
}

function ClickPicker({ onPick }: { onPick?: (latitude: number, longitude: number) => void }) {
  useMapEvents({
    click(event) {
      onPick?.(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

export default function ServiceMap({
  markers,
  center,
  zoom = 13,
  selectedId,
  userLocation,
  radiusKm,
  fitSignature,
  onBounds,
  onSelect,
  onPick,
}: Props) {
  const points = useMemo(
    () => markers.map((item) => [item.latitude, item.longitude] as [number, number]),
    [markers],
  );
  const selected = markers.find((item) => item.id === selectedId) ?? null;

  return (
    <MapContainer center={center} zoom={zoom} className="h-full w-full" scrollWheelZoom zoomControl={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {onBounds && <BoundsReporter onBounds={onBounds} />}
      {onPick && <ClickPicker onPick={onPick} />}
      <FitTo signature={fitSignature} points={points} />
      <FlyToSelected position={selected ? [selected.latitude, selected.longitude] : null} />
      {userLocation && radiusKm ? (
        <Circle
          center={userLocation}
          radius={radiusKm * 1000}
          pathOptions={{ color: "#1f6f5b", weight: 1.5, fillOpacity: 0.08 }}
        />
      ) : null}
      {userLocation ? (
        <CircleMarker
          center={userLocation}
          radius={7}
          pathOptions={{ color: "#1c1915", fillColor: "#7dd3c7", fillOpacity: 1, weight: 2 }}
        />
      ) : null}
      {markers.map((service) => (
        <Marker
          key={service.id}
          position={[service.latitude, service.longitude]}
          icon={iconFor(service.category, service.id === selectedId)}
          eventHandlers={{ click: () => onSelect?.(service.id) }}
        >
          <Popup>
            <div className="min-w-[180px] space-y-1">
              <p className="text-sm font-semibold">{service.name}</p>
              <p className="text-xs uppercase tracking-wide text-neutral-500">{categoryMeta(service.category).label}</p>
              {service.rating != null ? <p className="text-sm">Rating {service.rating.toFixed(1)}</p> : null}
              {formatDistance(service.distance_km) ? (
                <p className="text-sm">{formatDistance(service.distance_km)} away</p>
              ) : null}
              <a className="inline-block pt-1 text-sm font-medium text-moss underline" href={`/services/${service.id}`}>
                View details
              </a>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
