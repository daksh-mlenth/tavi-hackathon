// Quote type for vendor quotes
export interface Quote {
  id: string
  work_order_id: string
  vendor_id: string
  price: number | null
  availability_date: string | null
  quote_text: string | null
  status: string
  composite_score: number | null
  quality_score: number | null
  availability_score: number | null
  created_at: string
  updated_at: string
  vendor?: Vendor
}

// Vendor type
export interface Vendor {
  id: string
  business_name: string
  trade_type: string
  phone: string | null
  email: string | null
  address: string | null
  google_rating: number | null
  google_review_count: number | null
  yelp_rating: number | null
  yelp_review_count: number | null
  composite_score: number | null
  price_level: string | null
  service_radius_km: number | null
  is_verified: boolean
  created_at: string
}

// Work Order type
export interface WorkOrder {
  id: string
  title: string
  description: string
  raw_input: string
  trade_type: string
  work_type: string
  urgency: string
  priority: string
  category: string
  recurrence: string
  status: string
  location_address: string | null
  preferred_date: string | null
  estimated_duration: string | null
  special_requirements: string | null
  parts_materials: string[] | null
  asset_name: string | null
  asset_type: string | null
  customer_name: string | null
  customer_email: string | null
  customer_phone: string | null
  currency: string | null
  facility_manager_name: string | null
  facility_manager_email: string | null
  facility_confirmed: string | null
  vendor_dispatch_confirmed: string | null
  selected_vendor_id: string | null
  created_at: string
  updated_at: string
  quotes?: Quote[]
  selected_vendor?: Vendor
}

// Communication log type
export interface CommunicationLog {
  id: string
  work_order_id: string
  vendor_id: string | null
  channel: 'sms' | 'email' | 'phone'
  direction: 'inbound' | 'outbound'
  message: string
  sent_successfully: boolean
  metadata: Record<string, any> | null
  created_at: string
}
