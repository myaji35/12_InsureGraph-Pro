/**
 * Customer Types
 *
 * Story 3.4: Customer Portfolio Management
 */

export type Gender = 'M' | 'F' | 'O'
export type PolicyStatus = 'active' | 'expired' | 'cancelled' | 'pending'
export type PolicyType = 'life' | 'health' | 'car' | 'home' | 'accident' | 'other'

export interface Customer {
  id: string
  fp_user_id: string
  name: string
  birth_year: number
  gender: Gender
  phone?: string
  email?: string
  occupation?: string
  last_contact_date?: string
  notes?: string
  consent_given: boolean
  created_at: string
  updated_at: string
  age: number
  policy_count: number
}

export interface CustomerPolicy {
  id: string
  customer_id: string
  policy_name: string
  insurer: string
  policy_type?: PolicyType
  coverage_amount?: number
  premium_amount?: number
  start_date?: string
  end_date?: string
  status: PolicyStatus
  notes?: string
  document_id?: string
  created_at: string
  updated_at: string
}

export interface CustomerWithPolicies extends Customer {
  policies: CustomerPolicy[]
}

export interface CustomerListResponse {
  customers: Customer[]
  total: number
  page: number
  page_size: number
}

export interface CoverageSummary {
  total_coverage: number
  total_premium: number
  active_policies: number
  expired_policies: number
  coverage_by_type: Record<string, number>
  gaps: string[]
  recommendations: string[]
}

export interface CustomerCreateInput {
  name: string
  birth_year: number
  gender: Gender
  phone?: string
  email?: string
  occupation?: string
  notes?: string
  consent_given: boolean
}

export interface CustomerUpdateInput {
  name?: string
  birth_year?: number
  gender?: Gender
  phone?: string
  email?: string
  occupation?: string
  last_contact_date?: string
  notes?: string
  consent_given?: boolean
}
