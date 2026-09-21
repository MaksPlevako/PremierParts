// Mirrors the Django API contracts (see backend apps/*/views.py).

export type StockStatus = "in_stock" | "on_order" | "out_of_stock";

export interface ProductCard {
  id: number;
  slug: string;
  name: string;
  sku: string;
  manufacturer: string | null;
  image: string | null;
  price: number;
  sale_price: number | null;
  old_price: number | null;
  discount_percent: number | null;
  promotion_id: number | null;
  stock_status: StockStatus;
  generation_ids: number[];
  category: { slug: string; name: string };
  exact?: boolean;
}

export interface CarRef {
  generation_id: number;
  make: string;
  make_slug: string;
  model: string;
  model_slug: string;
  generation_slug: string;
  label: string;
  full_label: string;
  years_label: string;
  market: string;
}

export interface UnderstoodCar {
  make: string;
  make_slug?: string;
  label: string;
  full_label?: string;
  model_slug?: string | null;
  generation_id?: number;
  models?: { id: number; name: string; slug: string }[];
}

export interface ProductDetail extends ProductCard {
  description: string;
  side: "left" | "right" | "both" | "none";
  position: "front" | "rear" | "none";
  condition: string;
  images: { url: string; alt: string }[];
  part_numbers: { number: string; kind: "sku" | "oem" | "cross" }[];
  fitments: CarRef[];
  promotion: { slug: string; title: string } | null;
  breadcrumbs: { name: string; href: string }[];
  related: ProductCard[];
  updated_at: string;
}

export interface CategoryNode {
  id: number;
  slug: string;
  name: string;
  icon: string;
  image: string | null;
  product_count: number;
  children: CategoryNode[];
  description?: string;
  parent?: { slug: string; name: string } | null;
}

export interface Make {
  id: number;
  name: string;
  slug: string;
  logo: string | null;
  is_popular: boolean;
  product_count: number;
}

export interface GenerationItem {
  id: number;
  slug: string;
  label: string;
  years_label: string;
  year_from: number | null;
  year_to: number | null;
  product_count: number;
}

export interface CarModelItem {
  id: number;
  name: string;
  slug: string;
  market: string;
  product_count: number;
  generations: GenerationItem[];
}

export interface MakeDetail {
  id: number;
  name: string;
  slug: string;
  logo: string | null;
  families: { family: string; models: CarModelItem[] }[];
}

export interface ModelDetail {
  id: number;
  name: string;
  slug: string;
  family: string;
  market: string;
  make: { name: string; slug: string };
  generations: GenerationItem[];
}

export interface CarDetail extends CarRef {
  categories: { id: number; slug: string; name: string; count: number }[];
}

export interface Banner {
  id: number;
  title: string;
  subtitle: string;
  eyebrow: string;
  image: string | null;
  image_mobile: string | null;
  link: string;
  cta_label: string;
  placement: "hero" | "bento" | "home_strip" | "catalog_top" | "product_side";
  theme: "dark" | "light" | "gold";
}

export interface Promotion {
  id: number;
  slug: string;
  title: string;
  description: string;
  discount_percent: number;
  image: string | null;
  starts_at: string | null;
  ends_at: string | null;
  products?: ProductCard[];
}

export interface Page {
  slug: string;
  title: string;
  body?: string;
  show_in_footer: boolean;
  seo_title: string;
  seo_description: string;
  updated_at: string;
}

export interface Phone {
  number: string;
  label: string;
  viber: boolean;
}

export interface SiteSettings {
  phones: Phone[];
  email: string;
  address: string;
  work_hours: string;
  map_embed_url: string;
  socials: Record<string, string>;
  iban_details: string;
  pickup_note: string;
  about_short: string;
  seo_title: string;
  seo_description: string;
}

export interface HomeData {
  banners: { hero: Banner[]; bento: Banner[]; home_strip: Banner[] };
  categories: CategoryNode[];
  featured: ProductCard[];
  popular_makes: Make[];
  promotions: Promotion[];
  stats: { products: number; makes: number };
}

export interface Understood {
  kind: "vin" | "part_number" | "text" | "empty";
  text: string;
  part_number: string | null;
  vin: string | null;
  category: { id: number; slug: string; name: string } | null;
  car: UnderstoodCar | CarRef | null;
  side: string | null;
  position: string | null;
  year: number | null;
}

export interface VinDecodeResult {
  vin: string;
  valid: boolean;
  make: string | null;
  model: string | null;
  series: string | null;
  year: number | null;
  body: string | null;
  engine: string | null;
  country: string | null;
  market: string;
  source: "nhtsa" | "wmi";
  warnings: string[];
  matches: CarRef[];
  error?: string;
}

export interface ListingResult {
  count: number;
  page: number;
  page_size: number;
  pages: number;
  results: ProductCard[];
  facets: {
    categories: { id: number; slug: string; name: string; count: number }[];
    manufacturers: { id: number; name: string; count: number }[];
    side: { left: number; right: number };
    stock: { in_stock: number; on_order: number };
  };
  price_range: { min: number; max: number };
  understood: Understood | null;
  vin: VinDecodeResult | null;
  car: (CarRef | UnderstoodCar) | null;
  car_source: "page" | "query" | "my_car" | "vin" | null;
  relaxed: boolean;
  degraded: boolean;
}

export interface Suggest {
  kind: "vin" | "part_number" | "text" | "empty";
  part_number?: string | null;
  understood?: Understood | null;
  vin?: VinDecodeResult;
  car?: CarRef | UnderstoodCar | null;
  car_source?: string | null;
  products: ProductCard[];
  analogs?: ProductCard[];
  categories: { id: number; slug: string; name: string; count: number }[];
  total: number;
  relaxed?: boolean;
}

export interface OrderSummary {
  number: string;
  kind: "regular" | "quick";
  status: string;
  status_label: string;
  customer_name: string;
  phone: string;
  email: string;
  delivery_method: string;
  delivery_label: string;
  city: string;
  np_branch: string;
  address: string;
  payment_method: string;
  payment_label: string;
  comment: string;
  car: CarRef | null;
  subtotal: number;
  discount: number;
  total: number;
  created_at: string;
  items: {
    product_id: number | null;
    slug: string | null;
    name: string;
    sku: string;
    price: number;
    old_price: number | null;
    qty: number;
    line_total: number;
  }[];
}

export type ListingQuery = Partial<{
  q: string;
  category: string;
  make: string;
  model: string;
  generation: string | number;
  car: string | number;
  all_cars: string;
  manufacturer: string;
  side: string;
  stock: string;
  price_min: string;
  price_max: string;
  promo: string;
  sort: string;
  page: string | number;
  page_size: string | number;
}>;
