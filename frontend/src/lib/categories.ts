import type { CategoryId } from "./types";

export const CATEGORIES: { id: CategoryId; label: string; color: string }[] = [
  { id: "hospital", label: "Hospitals", color: "#9f2d2d" },
  { id: "atm", label: "ATMs", color: "#1d4e89" },
  { id: "shop", label: "Shops", color: "#b8612a" },
  { id: "other", label: "Others", color: "#1f6f5b" },
];

export function categoryMeta(id: string) {
  return CATEGORIES.find((item) => item.id === id) ?? CATEGORIES[3];
}

export function formatDistance(km?: number | null) {
  if (km == null) return null;
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(km < 10 ? 1 : 0)} km`;
}

export const CITY_CENTER = { latitude: 12.9716, longitude: 77.5946 };
