import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Work Orders
  createWorkOrder: async (data: {
    raw_input: string
    customer_name?: string
    customer_email?: string
    customer_phone?: string
  }) => {
    const response = await apiClient.post('/api/work-orders', data)
    return response.data
  },

  getWorkOrder: async (id: string) => {
    const response = await apiClient.get(`/api/work-orders/${id}`)
    return response.data
  },

  updateWorkOrderStatus: async (id: string, status: string) => {
    const response = await apiClient.patch(`/api/work-orders/${id}/status`, { status })
    return response.data
  },

  listWorkOrders: async (skip = 0, limit = 100) => {
    const response = await apiClient.get('/api/work-orders', {
      params: { skip, limit },
    })
    return response.data
  },

  discoverVendors: async (workOrderId: string) => {
    const response = await apiClient.post(`/api/work-orders/${workOrderId}/discover-vendors`)
    return response.data
  },

  contactVendors: async (workOrderId: string) => {
    const response = await apiClient.post(`/api/work-orders/${workOrderId}/contact-vendors`)
    return response.data
  },

  // Vendors
  listVendors: async (tradeType?: string) => {
    const response = await apiClient.get('/api/vendors', {
      params: tradeType ? { trade_type: tradeType } : {},
    })
    return response.data
  },

  getVendor: async (id: string) => {
    const response = await apiClient.get(`/api/vendors/${id}`)
    return response.data
  },

  // Quotes
  getQuotesForWorkOrder: async (workOrderId: string) => {
    const response = await apiClient.get(`/api/quotes/work-order/${workOrderId}`)
    return response.data
  },

  requestQuote: async (quoteId: string) => {
    const response = await apiClient.post(`/api/quotes/${quoteId}/request`)
    return response.data
  },

  requestMultipleQuotes: async (quoteIds: string[]) => {
    const response = await apiClient.post(`/api/quotes/request-multiple`, quoteIds)
    return response.data
  },

  acceptQuote: async (quoteId: string) => {
    const response = await apiClient.post(`/api/quotes/${quoteId}/accept`)
    return response.data
  },

  // Vendor Confirmation (new two-step process)
  confirmVendor: async (quoteId: string, facilityManagerEmail: string, facilityManagerName: string = 'Facility Manager') => {
    const response = await apiClient.post('/api/confirmations/confirm-vendor', {
      quote_id: quoteId,
      facility_manager_email: facilityManagerEmail,
      facility_manager_name: facilityManagerName
    })
    return response.data
  },

  facilityManagerConfirm: async (workOrderId: string, response: string) => {
    const res = await apiClient.post(`/api/confirmations/facility-confirm/${workOrderId}`, { response })
    return res.data
  },

  vendorDispatchConfirm: async (workOrderId: string, response: string) => {
    const res = await apiClient.post(`/api/confirmations/vendor-dispatch-confirm/${workOrderId}`, { response })
    return res.data
  },

  // Communications
  getCommunicationsForWorkOrder: async (workOrderId: string) => {
    const response = await apiClient.get(`/api/communications/work-order/${workOrderId}`)
    return response.data
  },

  // Demo endpoints for testing bidirectional conversations
  simulateVendorReply: async (quoteId: string, message: string, channel: 'email' | 'sms') => {
    const response = await apiClient.post('/api/demo/simulate-vendor-reply', {
      quote_id: quoteId,
      reply_message: message,
      channel: channel
    })
    return response.data
  },

  simulateMultipleQuotes: async (workOrderId: string) => {
    const response = await apiClient.post(`/api/demo/simulate-multiple-quotes`, null, {
      params: { work_order_id: workOrderId }
    })
    return response.data
  },

  simulateFacilityConfirmation: async (workOrderId: string, approved: boolean) => {
    const response = await apiClient.post('/api/demo/simulate-facility-confirmation', {
      work_order_id: workOrderId,
      approved
    })
    return response.data
  },

  simulateVendorDispatchConfirmation: async (workOrderId: string, confirmed: boolean) => {
    const response = await apiClient.post('/api/demo/simulate-vendor-dispatch-confirmation', {
      work_order_id: workOrderId,
      confirmed
    })
    return response.data
  }
}
