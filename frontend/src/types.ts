export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string;
  role: 'admin' | 'manager' | 'cashier' | 'stock_manager';
  is_active: boolean;
  created_at?: string;
}

export interface Category {
  id: number;
  name: string;
  description: string;
  icon: string;
  display_order: number;
  product_count: number;
}

export interface Product {
  id: number;
  name: string;
  category_id: number;
  category_name: string;
  section: string;
  price: number;
  description: string;
  image_url: string;
  is_available: boolean;
  stock_quantity: number;
  low_stock_threshold: number;
}

export interface TableItem {
  id: number;
  number: number;
  section: string;
  capacity: number;
  status: 'available' | 'occupied' | 'reserved';
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  discount_pct: number;
  subtotal: number;
  notes: string;
}

export interface Order {
  id: number;
  table_id: number | null;
  table_number: number | null;
  customer_id: number | null;
  cashier_id: number;
  cashier_name: string;
  status: 'draft' | 'in_progress' | 'served' | 'paid' | 'cancelled';
  total_amount: number;
  discount_pct: number;
  discount_amount: number;
  notes: string;
  cancel_reason: string;
  items: OrderItem[];
  created_at?: string;
}

export interface AnomalyAlert {
  id: number;
  order_id: string;
  risk_score: number;
  risk_level: 'NORMAL' | 'ALERTE' | 'CRITIQUE';
  predicted_label: number;
  anomaly_type: string;
  reason_codes: string;
  alert_explanation: string;
  model_name: string;
  status: string;
  assigned_to: number | null;
  assigned_to_name: string;
  created_at?: string;
  comments_count: number;
}

export interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  archetype: string;
  price_tier: string;
  time_preference: string;
  day_preference: string;
  visit_count: number;
  total_spent: number;
  last_visit?: string;
}

export interface DashboardKPIs {
  total_orders: number;
  total_revenue: number;
  today_orders: number;
  today_revenue: number;
  avg_basket: number;
  active_orders: number;
  low_stock_count: number;
  top_products: { name: string; quantity: number; revenue: number }[];
  payment_methods: { method: string; count: number; total: number }[];
}

export interface Recommendation {
  product_name: string;
  score: number;
  confidence: number;
  lift: number;
  support: number;
  source: string[];
  antecedents: string[];
  explanation: string;
}

// Cart types for POS
export interface CartItem {
  product: Product;
  quantity: number;
  notes: string;
}
