export type CategoryId = "hospital" | "atm" | "shop" | "other";

export type ServiceMetadata = {
  address?: string;
  phone?: string;
  description?: string;
  [key: string]: unknown;
};

export type Service = {
  id: string;
  name: string;
  category: CategoryId;
  latitude: number;
  longitude: number;
  rating: number | null;
  metadata: ServiceMetadata | null;
  created_at: string;
  updated_at: string;
  distance_km?: number | null;
};

export type ServicePage = {
  items: Service[];
  total: number;
  page: number;
  page_size: number;
};

export type NearbyResponse = {
  items: Service[];
  latitude: number;
  longitude: number;
  radius_km: number;
  count: number;
};

export type MapResponse = {
  items: Service[];
  count: number;
  truncated: boolean;
};

export type StatsResponse = {
  total: number;
  by_category: { category: CategoryId; count: number }[];
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type Admin = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
};

export type BulkResult = {
  created: number;
  failed: number;
  errors: { row: number | null; message: string }[];
};

export type ServiceInput = {
  name: string;
  category: CategoryId;
  latitude: number;
  longitude: number;
  rating?: number | null;
  clear_rating?: boolean;
  metadata?: ServiceMetadata | null;
};

export type Bounds = {
  min_lat: number;
  min_lng: number;
  max_lat: number;
  max_lng: number;
};
