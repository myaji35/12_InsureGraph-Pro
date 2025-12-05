/**
 * Customer API Client
 *
 * Story 3.4: Customer Portfolio Management
 */

import { Customer, CustomerWithPolicies, CustomerListResponse, CoverageSummary, CustomerCreateInput, CustomerUpdateInput, CustomerPolicy } from '@/types/customer'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:3030/api'

async function getAuthHeaders(): Promise<HeadersInit> {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }
}

export async function fetchCustomers(params?: {
  search?: string
  gender?: string
  min_age?: number
  max_age?: number
  page?: number
  page_size?: number
}): Promise<CustomerListResponse> {
  const queryParams = new URLSearchParams()
  if (params?.search) queryParams.append('search', params.search)
  if (params?.gender) queryParams.append('gender', params.gender)
  if (params?.min_age !== undefined) queryParams.append('min_age', params.min_age.toString())
  if (params?.max_age !== undefined) queryParams.append('max_age', params.max_age.toString())
  if (params?.page) queryParams.append('page', params.page.toString())
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString())

  const url = `${API_BASE}/api/v1/customers?${queryParams.toString()}`
  const response = await fetch(url, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch customers: ${response.statusText}`)
  }

  return response.json()
}

export async function getCustomer(customerId: string): Promise<CustomerWithPolicies> {
  const response = await fetch(`${API_BASE}/api/v1/customers/${customerId}`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch customer: ${response.statusText}`)
  }

  return response.json()
}

export async function createCustomer(data: CustomerCreateInput): Promise<Customer> {
  const response = await fetch(`${API_BASE}/api/v1/customers`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create customer')
  }

  return response.json()
}

export async function updateCustomer(customerId: string, data: CustomerUpdateInput): Promise<Customer> {
  const response = await fetch(`${API_BASE}/api/v1/customers/${customerId}`, {
    method: 'PUT',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(`Failed to update customer: ${response.statusText}`)
  }

  return response.json()
}

export async function deleteCustomer(customerId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/customers/${customerId}`, {
    method: 'DELETE',
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to delete customer: ${response.statusText}`)
  }
}

export async function getCoverageSummary(customerId: string): Promise<CoverageSummary> {
  const response = await fetch(`${API_BASE}/api/v1/customers/${customerId}/coverage`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch coverage summary: ${response.statusText}`)
  }

  return response.json()
}
