'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { api } from '@/lib/api'
import QuoteComparisonDashboard from '@/components/QuoteComparisonDashboard'
import RequestQuoteModal from '@/components/RequestQuoteModal'
import AutomationTimeline from '@/components/AutomationTimeline'
import { 
  Building2, MapPin, Calendar, Loader2, Phone, Mail, MessageSquare,
  DollarSign, Star, Clock, CheckCircle, ArrowLeft, AlertTriangle,
  Wrench, Package, FileText, RefreshCw, Zap, Users
} from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function WorkOrderDetail() {
  const router = useRouter()
  const params = useParams()
  const workOrderId = params.id as string

  const [workOrder, setWorkOrder] = useState<any>(null)
  const [quotes, setQuotes] = useState<any[]>([])
  const [communications, setCommunications] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedVendors, setSelectedVendors] = useState<Set<string>>(new Set())
  const [visibleVendorCount, setVisibleVendorCount] = useState(5)  // Show 5 initially
  const [expandedComm, setExpandedComm] = useState<string | null>(null)  // Track expanded communication
  const [requestQuoteModal, setRequestQuoteModal] = useState<{
    isOpen: boolean
    quoteIds: string[]
    vendorNames: string[]
  }>({ isOpen: false, quoteIds: [], vendorNames: [] })
  const [showAutomation, setShowAutomation] = useState(false)
  const [automationRunning, setAutomationRunning] = useState(false)

  useEffect(() => {
    if (workOrderId) {
      loadWorkOrderData()
      const interval = setInterval(() => {
        if (!automationRunning) {
          loadWorkOrderData()
        }
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [workOrderId, automationRunning])

  const loadWorkOrderData = async () => {
    try {
      const [woData, quotesData, commsData] = await Promise.all([
        api.getWorkOrder(workOrderId),
        api.getQuotesForWorkOrder(workOrderId),
        api.getCommunicationsForWorkOrder(workOrderId),
      ])
      
      setWorkOrder(woData)
      setQuotes(quotesData.quotes || [])
      setCommunications(commsData || [])
    } catch (error) {
      console.error('Failed to load work order data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAcceptQuote = async (quoteId: string) => {
    try {
      await api.acceptQuote(quoteId)
      toast.success('Quote accepted! Vendor has been dispatched.')
      loadWorkOrderData()
    } catch (error) {
      toast.error('Failed to accept quote')
    }
  }

  const toggleVendorSelection = (quoteId: string) => {
    const newSelection = new Set(selectedVendors)
    if (newSelection.has(quoteId)) {
      newSelection.delete(quoteId)
    } else {
      newSelection.add(quoteId)
    }
    setSelectedVendors(newSelection)
  }

  const handleRequestQuotesForSelected = () => {
    if (selectedVendors.size === 0) return
    
    const quoteIds = Array.from(selectedVendors)
    const vendorNames = quotes
      .filter(q => selectedVendors.has(q.id))
      .map(q => (q as any).vendor?.business_name || 'Vendor')
    
    setRequestQuoteModal({
      isOpen: true,
      quoteIds,
      vendorNames
    })
  }

  const handleRequestSingleQuote = (quoteId: string, vendorName: string) => {
    setRequestQuoteModal({
      isOpen: true,
      quoteIds: [quoteId],
      vendorNames: [vendorName]
    })
  }

  const handleRealQuoteRequest = async () => {
    try {
      if (requestQuoteModal.quoteIds.length === 1) {
        await api.requestQuote(requestQuoteModal.quoteIds[0])
        toast.success(`Quote request sent to ${requestQuoteModal.vendorNames[0]}!`)
      } else {
        await api.requestMultipleQuotes(requestQuoteModal.quoteIds)
        toast.success(`Quote requests sent to ${requestQuoteModal.quoteIds.length} vendors!`)
      }
      setSelectedVendors(new Set())
      loadWorkOrderData()
    } catch (error) {
      toast.error('Failed to request quotes')
    }
  }

  const handleLoadMore = () => {
    setVisibleVendorCount(prev => prev + 5)  // Load 5 more vendors
  }

  const handleSimulateTop5Vendors = async () => {
    try {
      const top5Quotes = quotes
        .filter(q => q.status === 'pending')
        .slice(0, 5)
      
      if (top5Quotes.length === 0) {
        toast.error('No pending quotes to simulate')
        return
      }

      for (const quote of top5Quotes) {
        const vendorMessage = `Hi, I can do this for $${Math.floor(Math.random() * 300) + 200}. Available in ${Math.floor(Math.random() * 5) + 1} days.`
        await api.simulateVendorReply(quote.id, vendorMessage, 'sms')
      }
      
      toast.success(`🎭 Simulated ${top5Quotes.length} vendor responses!`)
      setTimeout(() => loadWorkOrderData(), 2000)
    } catch (error) {
      toast.error('Failed to simulate responses')
    }
  }
  
  const handleLetAIHandle = () => {
    if (showAutomation || automationRunning) {
      console.log('Automation already running, ignoring click')
      return
    }
    setShowAutomation(true)
    setAutomationRunning(true)
  }
  
  const handleAutomationComplete = () => {
    toast.success('🎉 AI successfully completed the workflow!')
    setShowAutomation(false)
    setAutomationRunning(false)
    loadWorkOrderData()
  }
  
  const handleAutomationError = (error: string) => {
    toast.error(`Automation failed: ${error}`)
    setAutomationRunning(false)
  }

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email': return <Mail className="h-4 w-4" />
      case 'sms': return <MessageSquare className="h-4 w-4" />
      case 'phone': return <Phone className="h-4 w-4" />
      default: return <MessageSquare className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    )
  }

  if (!workOrder) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">Work order not found</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="mt-4 text-blue-600 hover:text-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="h-6 w-6" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{workOrder.title}</h1>
                <p className="text-sm text-gray-500">Work Order #{workOrder.id.slice(0, 8)}</p>
              </div>
            </div>
            <span className="px-4 py-2 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {workOrder.status.replace(/_/g, ' ')}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Work Order Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Details Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Details</h2>
              
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Description</p>
                  <p className="text-gray-900">{workOrder.description}</p>
                </div>

                {/* Core Information Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Trade Type</p>
                    <p className="text-gray-900 font-medium uppercase">{workOrder.trade_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1 flex items-center">
                      <AlertTriangle className="h-4 w-4 mr-1" />
                      Urgency
                    </p>
                    <p className="text-gray-900 font-medium capitalize">{workOrder.urgency}</p>
                  </div>
                  {workOrder.priority && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Priority</p>
                      <p className="text-gray-900 font-medium capitalize">{workOrder.priority}</p>
                    </div>
                  )}
                </div>

                {/* Work Classification */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {workOrder.work_type && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1 flex items-center">
                        <Wrench className="h-4 w-4 mr-1" />
                        Work Type
                      </p>
                      <p className="text-gray-900 font-medium capitalize">{workOrder.work_type}</p>
                    </div>
                  )}
                  {workOrder.category && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Category</p>
                      <p className="text-gray-900 font-medium capitalize">{workOrder.category.replace(/_/g, ' ')}</p>
                    </div>
                  )}
                  {workOrder.recurrence && workOrder.recurrence !== 'none' && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1 flex items-center">
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Recurrence
                      </p>
                      <p className="text-gray-900 font-medium capitalize">{workOrder.recurrence}</p>
                    </div>
                  )}
                </div>

                {/* Asset Information */}
                {workOrder.asset_name && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm font-medium text-blue-900 mb-2 flex items-center">
                      <Building2 className="h-4 w-4 mr-1" />
                      Asset Details
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-blue-700">Asset Name</p>
                        <p className="text-sm text-blue-900 font-medium">{workOrder.asset_name}</p>
                      </div>
                      {workOrder.asset_type && (
                        <div>
                          <p className="text-xs text-blue-700">Asset Type</p>
                          <p className="text-sm text-blue-900 font-medium">{workOrder.asset_type}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Location */}
                <div>
                  <p className="text-sm text-gray-600 mb-1 flex items-center">
                    <MapPin className="h-4 w-4 mr-1" />
                    Location
                  </p>
                  <p className="text-gray-900">{workOrder.location_address}</p>
                  {(workOrder.location_city || workOrder.location_state || workOrder.location_zip) && (
                    <p className="text-gray-600 text-sm mt-1">
                      {[workOrder.location_city, workOrder.location_state, workOrder.location_zip].filter(Boolean).join(', ')}
                    </p>
                  )}
                </div>

                {/* Scheduling Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {workOrder.preferred_date && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1 flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        Preferred Date
                      </p>
                      <p className="text-gray-900">{format(new Date(workOrder.preferred_date), 'PPP')}</p>
                    </div>
                  )}
                  {workOrder.due_date && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1 flex items-center">
                        <Calendar className="h-4 w-4 mr-1 text-red-500" />
                        Due Date
                      </p>
                      <p className="text-gray-900 font-medium">{format(new Date(workOrder.due_date), 'PPP')}</p>
                    </div>
                  )}
                  {workOrder.estimated_hours && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1 flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        Est. Duration
                      </p>
                      <p className="text-gray-900">{workOrder.estimated_hours} hours</p>
                    </div>
                  )}
                </div>

                {/* Parts Needed */}
                {workOrder.parts_needed && workOrder.parts_needed.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-600 mb-2 flex items-center">
                      <Package className="h-4 w-4 mr-1" />
                      Parts Needed
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {workOrder.parts_needed.map((part: string, idx: number) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                        >
                          {part}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Special Requirements */}
                {workOrder.special_requirements && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-sm font-medium text-yellow-900 mb-1 flex items-center">
                      <Zap className="h-4 w-4 mr-1" />
                      Special Requirements
                    </p>
                    <p className="text-sm text-yellow-800">{workOrder.special_requirements}</p>
                  </div>
                )}

                {/* Customer Information */}
                {(workOrder.customer_name || workOrder.customer_email || workOrder.customer_phone) && (
                  <div className="border-t pt-4">
                    <p className="text-sm text-gray-600 mb-3 flex items-center">
                      <Users className="h-4 w-4 mr-1" />
                      Customer Information
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {workOrder.customer_name && (
                        <div>
                          <p className="text-xs text-gray-500">Name</p>
                          <p className="text-sm text-gray-900">{workOrder.customer_name}</p>
                        </div>
                      )}
                      {workOrder.customer_email && (
                        <div>
                          <p className="text-xs text-gray-500">Email</p>
                          <p className="text-sm text-gray-900">{workOrder.customer_email}</p>
                        </div>
                      )}
                      {workOrder.customer_phone && (
                        <div>
                          <p className="text-xs text-gray-500">Phone</p>
                          <p className="text-sm text-gray-900">{workOrder.customer_phone}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Demo Button - For testing bidirectional conversations */}
            {quotes.filter(q => q.status === 'pending').length >= 5 && quotes.filter(q => q.status === 'received').length < 3 && (
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-purple-900 flex items-center">
                      <Zap className="h-5 w-5 mr-2" />
                      🤖 Tavi AI Agent: Autonomous Workflow
                    </h3>
                    <p className="text-sm text-purple-700 mt-1">
                      AI handles everything end-to-end: vendor discovery, quote negotiation, and dispatch approval
                    </p>
                  </div>
                  <button
                    onClick={handleLetAIHandle}
                    disabled={automationRunning}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-6 py-2.5 rounded-lg font-semibold transition-all shadow-md hover:shadow-lg flex items-center text-sm disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    {automationRunning ? 'Running...' : 'Let Tavi Handle'}
                  </button>
                </div>
              </div>
            )}

            {/* AI Recommendation & Comparison CTA */}
            {quotes.filter(q => q.price).length >= 2 && (
              <div className="space-y-4">
                {/* AI Recommendation */}
                {(() => {
                  const receivedQuotes = quotes.filter(q => q.price)
                  if (receivedQuotes.length === 0) return null
                  
                  // Find best vendor using composite score (price + quality + availability)
                  const bestValue = receivedQuotes.reduce((best, current) => {
                    // Use the backend's composite_score which already weighs all 3 factors
                    const bestComposite = best.composite_score || 0
                    const currentComposite = current.composite_score || 0
                    return currentComposite > bestComposite ? current : best
                  })
                  
                  // Check if vendor already selected
                  const isVendorSelected = workOrder?.status === 'dispatched' || workOrder?.status === 'completed'
                  
                  return (
                    <div className={`bg-gradient-to-r ${
                      isVendorSelected 
                        ? 'from-green-50 to-emerald-50 border-green-200' 
                        : 'from-blue-50 to-purple-50 border-blue-200'
                    } border-2 rounded-lg p-6`}>
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          <div className={`h-10 w-10 ${
                            isVendorSelected ? 'bg-green-600' : 'bg-blue-600'
                          } rounded-full flex items-center justify-center`}>
                            <span className="text-white text-xl">
                              {isVendorSelected ? '✓' : '🤖'}
                            </span>
                          </div>
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {isVendorSelected ? 'Selected Vendor' : 'AI Recommendation'}
                          </h3>
                          <p className="text-gray-700 mb-4">
                            {isVendorSelected ? 'You selected ' : 'Based on price, ratings, and availability, we recommend '}
                            <span className="font-bold text-blue-700">{bestValue.vendor?.business_name}</span>
                            {' '}at{' '}
                            <span className="font-bold text-green-700">
                              {workOrder?.currency_symbol}{bestValue.price}
                            </span>
                            .
                          </p>
                          <button
                            onClick={() => router.push(`/quotes/${workOrderId}`)}
                            className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center space-x-2 shadow-lg"
                          >
                            <span>📊</span>
                            <span>{isVendorSelected ? 'View Quote Comparison History' : 'View Detailed Comparison & Select Vendor'}</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })()}
              </div>
            )}

            {/* Service Providers - Top Vendors */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    Top Service Providers ({quotes.length})
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Found within 30 minutes • Scored from Google & Yelp
                  </p>
                </div>
                {selectedVendors.size > 0 && (
                  <span className="text-sm font-medium text-blue-600">
                    {selectedVendors.size} selected
                  </span>
                )}
              </div>

              {quotes.length === 0 ? (
                <div className="text-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
                  <p className="text-gray-500">Discovering service providers...</p>
                </div>
              ) : (
                <>
                  <div className="space-y-4 mt-4">
                    {quotes
                      .sort((a, b) => ((b.vendor as any)?.composite_score || 0) - ((a.vendor as any)?.composite_score || 0))
                      .slice(0, visibleVendorCount)
                      .map((quote, index) => (
                      <div
                        key={quote.id}
                        className={`border rounded-lg p-5 transition-all ${
                          quote.status === 'accepted' 
                            ? 'border-green-500 bg-green-50 shadow-md' 
                            : selectedVendors.has(quote.id)
                            ? 'border-blue-500 bg-blue-50 shadow-md'
                            : 'border-gray-200 hover:border-blue-300 hover:shadow-sm'
                        }`}
                      >
                        {/* Vendor Header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <div className="flex items-center mb-2">
                              {/* Checkbox for multi-select - only show for pending quotes */}
                              {quote.status === 'pending' && (
                                <input
                                  type="checkbox"
                                  checked={selectedVendors.has(quote.id)}
                                  onChange={() => toggleVendorSelection(quote.id)}
                                  className="w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 mr-3 cursor-pointer"
                                />
                              )}
                              {/* Badge for requested status */}
                              {quote.status === 'requested' && (
                                <div className="bg-blue-500 text-white rounded-full px-3 py-1 text-xs font-bold mr-3">
                                  REQUESTED
                                </div>
                              )}
                              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm mr-3">
                                #{index + 1}
                              </div>
                              <div>
                                <h3 className="font-bold text-lg text-gray-900">
                                  {(quote as any).vendor?.business_name || 'Service Provider'}
                                </h3>
                                {(quote as any).vendor?.trade_specialties && (quote as any).vendor.trade_specialties.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mt-1">
                                    {(quote as any).vendor.trade_specialties.map((specialty: string, idx: number) => (
                                      <span
                                        key={idx}
                                        className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full"
                                      >
                                        {specialty.toUpperCase()}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Quality Score - Prominent Display */}
                            {(quote as any).vendor?.composite_score !== undefined && (
                              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg px-4 py-3 mb-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex-1">
                                    <p className="text-xs text-yellow-800 font-medium mb-1">QUALITY SCORE</p>
                                    <div className="flex items-center">
                                      <div className="text-3xl font-bold text-yellow-900">
                                        {(quote as any).vendor.composite_score.toFixed(1)}
                                      </div>
                                      <div className="text-yellow-700 ml-2">/10</div>
                                    </div>
                                    {(quote as any).vendor?.price_level && (
                                      <div className="mt-2">
                                        <p className="text-xs text-yellow-700">Price Range</p>
                                        <p className="text-lg font-bold text-yellow-900">
                                          {(quote as any).vendor.price_level}
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                  <Star className="h-10 w-10 text-yellow-500 fill-current" />
                                </div>
                                <p className="text-xs text-yellow-700 mt-1">
                                  Aggregated from Google & Yelp reviews
                                </p>
                              </div>
                            )}

                            {/* Reviews Breakdown */}
                            <div className="grid grid-cols-2 gap-3 mb-3">
                              {/* Google Reviews */}
                              {(quote as any).vendor?.google_rating ? (
                                <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                  <div className="flex items-center mb-1">
                                    <div className="bg-blue-500 text-white rounded px-2 py-0.5 text-xs font-bold mr-2">
                                      Google
                                    </div>
                                  </div>
                                  <div className="flex items-center">
                                    <Star className="h-4 w-4 text-yellow-500 fill-current mr-1" />
                                    <span className="font-bold text-gray-900">
                                      {(quote as any).vendor.google_rating.toFixed(1)}
                                    </span>
                                    <span className="text-gray-600 text-sm ml-1">
                                      ({(quote as any).vendor.google_review_count || 0} reviews)
                                    </span>
                                  </div>
                                </div>
                              ) : (
                                <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                  <div className="flex items-center mb-1">
                                    <div className="bg-blue-500 text-white rounded px-2 py-0.5 text-xs font-bold mr-2">
                                      Google
                                    </div>
                                  </div>
                                  <p className="text-xs text-gray-500">No reviews yet</p>
                                </div>
                              )}

                              {/* Yelp Reviews */}
                              {(quote as any).vendor?.yelp_rating && (quote as any).vendor.yelp_rating > 0 ? (
                                <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                  <div className="flex items-center mb-1">
                                    <div className="bg-red-500 text-white rounded px-2 py-0.5 text-xs font-bold mr-2">
                                      Yelp
                                    </div>
                                  </div>
                                  <div className="flex items-center">
                                    <Star className="h-4 w-4 text-yellow-500 fill-current mr-1" />
                                    <span className="font-bold text-gray-900">
                                      {(quote as any).vendor.yelp_rating.toFixed(1)}
                                    </span>
                                    <span className="text-gray-600 text-sm ml-1">
                                      ({(quote as any).vendor.yelp_review_count || 0} reviews)
                                    </span>
                                  </div>
                                </div>
                              ) : (
                                <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                  <div className="flex items-center mb-1">
                                    <div className="bg-red-500 text-white rounded px-2 py-0.5 text-xs font-bold mr-2">
                                      Yelp
                                    </div>
                                  </div>
                                  <p className="text-xs text-gray-500">Not found on Yelp</p>
                                </div>
                              )}
                            </div>

                            {/* Contact & Location */}
                            <div className="space-y-2 mb-3">
                              {(quote as any).vendor?.address && (
                                <p className="text-sm text-gray-700 flex items-start">
                                  <MapPin className="h-4 w-4 mr-2 mt-0.5 text-gray-500 flex-shrink-0" />
                                  <span>
                                    {(quote as any).vendor.address}
                                    {(quote as any).vendor.city && `, ${(quote as any).vendor.city}`}
                                    {(quote as any).vendor.state && `, ${(quote as any).vendor.state}`}
                                  </span>
                                </p>
                              )}
                              {(quote as any).vendor?.phone && (
                                <p className="text-sm text-gray-700 flex items-center">
                                  <Phone className="h-4 w-4 mr-2 text-gray-500" />
                                  {(quote as any).vendor.phone}
                                </p>
                              )}
                            </div>
                          </div>

                          {/* Price Display */}
                          {quote.price ? (
                            <div className="text-right ml-4">
                              <p className="text-xs text-gray-500 mb-1">QUOTED PRICE</p>
                              <p className="text-3xl font-bold text-green-600">
                                {workOrder?.currency_symbol || '$'}{quote.price.toFixed(2)}
                              </p>
                            </div>
                          ) : (
                            <div className="text-right ml-4">
                              <p className="text-xs text-gray-500 mb-1">PRICE</p>
                              <p className="text-lg font-medium text-gray-400">
                                Not quoted yet
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Availability */}
                        {quote.availability_date && (
                          <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-3">
                            <p className="text-sm text-blue-900 flex items-center">
                              <Clock className="h-4 w-4 mr-2" />
                              <span className="font-medium">Available:</span>
                              <span className="ml-1">{format(new Date(quote.availability_date), 'PPPP')}</span>
                            </p>
                          </div>
                        )}

                        {/* Quote Text */}
                        {quote.quote_text && (
                          <div className="bg-gray-50 rounded-lg p-3 mb-3">
                            <p className="text-sm text-gray-700 italic">"{quote.quote_text}"</p>
                          </div>
                        )}

                        {/* Action Buttons */}
                        {quote.status === 'pending' && workOrder.status !== 'dispatched' && (
                          <button
                            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center font-semibold shadow-sm hover:shadow-md"
                            onClick={() => handleRequestSingleQuote(quote.id, (quote as any).vendor?.business_name || 'vendor')}
                          >
                            <MessageSquare className="h-5 w-5 mr-2" />
                            Request Quote from this Vendor
                          </button>
                        )}

                        {quote.status === 'requested' && workOrder.status !== 'dispatched' && (
                          <div className="space-y-3">
                            <div className="flex items-center justify-center text-blue-700 font-bold py-3 bg-blue-100 rounded-lg">
                              <Clock className="h-5 w-5 mr-2" />
                              Quote Requested - Waiting for Response
                            </div>
                            <button
                              className="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center font-medium"
                              onClick={() => handleRequestSingleQuote(quote.id, (quote as any).vendor?.business_name || 'vendor')}
                            >
                              <MessageSquare className="h-4 w-4 mr-2" />
                              Request Again
                            </button>
                          </div>
                        )}

                        {quote.status === 'received' && workOrder.status !== 'dispatched' && (
                          <button
                            onClick={() => handleAcceptQuote(quote.id)}
                            className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center font-semibold shadow-sm hover:shadow-md"
                          >
                            <CheckCircle className="h-5 w-5 mr-2" />
                            Accept Quote & Dispatch Vendor
                          </button>
                        )}

                        {quote.status === 'accepted' && (
                          <div className="flex items-center justify-center text-green-700 font-bold py-3 bg-green-100 rounded-lg">
                            <CheckCircle className="h-6 w-6 mr-2" />
                            ✓ Quote Accepted - Vendor Dispatched
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Load More Button */}
                  {visibleVendorCount < quotes.length && (
                    <div className="mt-6 text-center">
                      <button
                        onClick={handleLoadMore}
                        className="px-8 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors font-semibold shadow-sm hover:shadow-md"
                      >
                        Load More
                      </button>
                      <p className="text-sm text-gray-600 mt-3">
                        Showing {visibleVendorCount} of {quotes.length} service providers
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Floating Action Bar for Multi-Select */}
          {selectedVendors.size > 0 && (
            <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
              <div className="bg-blue-600 text-white rounded-full shadow-2xl px-8 py-4 flex items-center space-x-4">
                <span className="font-semibold">
                  {selectedVendors.size} vendor{selectedVendors.size > 1 ? 's' : ''} selected
                </span>
                <button
                  onClick={handleRequestQuotesForSelected}
                  className="bg-white text-blue-600 px-6 py-2 rounded-full font-bold hover:bg-blue-50 transition-colors flex items-center"
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Request Quotes
                </button>
                <button
                  onClick={() => setSelectedVendors(new Set())}
                  className="text-white hover:text-blue-200 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          )}

          {/* Right Column - Communication Stream */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6 sticky top-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Communication Stream
              </h2>

              {communications.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm">No communications yet</p>
                  <p className="text-gray-400 text-xs mt-1">Messages will appear here when you request quotes</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[700px] overflow-y-auto pr-2">
                  {/* Confirmation Communications (Facility Manager & Vendor Dispatch) */}
                  {(() => {
                    const confirmations = communications.filter(c => 
                      c.metadata?.type === 'facility_confirmation' || 
                      c.metadata?.type === 'vendor_dispatch_confirmation'
                    )
                    
                    if (confirmations.length > 0) {
                      return (
                        <div className="mb-4">
                          <h3 className="text-xs font-bold text-purple-700 uppercase mb-2 flex items-center">
                            <span className="bg-purple-100 px-2 py-1 rounded">
                              🔔 Confirmations
                            </span>
                          </h3>
                          <div className="space-y-2">
                            {confirmations
                              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                              .map((comm) => {
                                const isExpanded = expandedComm === comm.id
                                const isOutbound = comm.direction === 'outbound'
                                const isFacilityManager = comm.metadata?.type === 'facility_confirmation'
                                
                                return (
                                  <div
                                    key={comm.id}
                                    className={`border-l-4 ${
                                      isOutbound ? 'border-purple-500 bg-purple-50' : 'border-green-500 bg-green-50'
                                    } rounded-r-lg p-3 hover:shadow-sm transition-shadow cursor-pointer`}
                                    onClick={() => setExpandedComm(isExpanded ? null : comm.id)}
                                  >
                                    <div className="flex items-center justify-between mb-2">
                                      <div className="flex items-center space-x-2 flex-wrap">
                            <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full font-bold border border-blue-700">
                              {comm.channel.toUpperCase()}
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              isOutbound 
                                ? 'bg-purple-200 text-purple-800' 
                                : 'bg-green-200 text-green-800'
                            }`}>
                              {isOutbound 
                                ? (isFacilityManager ? '→ TO Manager' : '→ TO Vendor')
                                : (isFacilityManager ? '← FROM Manager' : '← FROM Vendor')
                              }
                            </span>
                            {!isFacilityManager && comm.vendor_name && (
                              <span className="text-xs font-semibold text-gray-900 bg-white px-2 py-0.5 rounded border border-gray-300">
                                {comm.vendor_name}
                              </span>
                            )}
                            {isFacilityManager && (
                              <span className="text-xs font-semibold text-gray-900 bg-yellow-100 px-2 py-0.5 rounded border border-yellow-300">
                                {workOrder?.facility_manager_name || 'Manager'}
                              </span>
                            )}
                                      </div>
                                      <span className="text-xs text-gray-500">
                                        {new Date(comm.timestamp).toLocaleTimeString()}
                                      </span>
                                    </div>
                                    <div className={`text-sm text-gray-800 ${isExpanded ? '' : 'line-clamp-2'}`}>
                                      {comm.message || comm.content}
                                    </div>
                                  </div>
                                )
                              })}
                          </div>
                        </div>
                      )
                    }
                    return null
                  })()}
                  
                  {/* Regular Quote Communications */}
                  {(() => {
                    const regularComms = communications.filter(c => 
                      !c.metadata?.type || 
                      (c.metadata?.type !== 'facility_confirmation' && c.metadata?.type !== 'vendor_dispatch_confirmation')
                    )
                    
                    if (regularComms.length > 0) {
                      return (
                        <>
                          <h3 className="text-xs font-bold text-blue-700 uppercase mb-2 flex items-center">
                            <span className="bg-blue-100 px-2 py-1 rounded">
                              💬 Quote Conversations
                            </span>
                          </h3>
                          <div className="space-y-3">
                            {regularComms
                              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                              .map((comm) => {
                      const isExpanded = expandedComm === comm.id
                      const isOutbound = comm.direction === 'outbound'
                      
                      return (
                        <div 
                          key={comm.id} 
                          className={`border-l-4 ${
                            isOutbound ? 'border-blue-500 bg-blue-50' : 'border-green-500 bg-green-50'
                          } rounded-r-lg p-3 hover:shadow-sm transition-shadow cursor-pointer`}
                          onClick={() => setExpandedComm(isExpanded ? null : comm.id)}
                        >
                          {/* Header */}
                          <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-2 flex-wrap">
                              {getChannelIcon(comm.channel)}
                              <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full font-bold border border-blue-700">
                                {comm.channel.toUpperCase()}
                              </span>
                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                isOutbound 
                                  ? 'bg-blue-200 text-blue-800' 
                                  : 'bg-green-200 text-green-800'
                              }`}>
                                {isOutbound ? '→ SENT' : '← RECEIVED'}
                              </span>
                              {comm.vendor_name && (
                                <span className="text-xs font-semibold text-gray-900 bg-white px-2 py-0.5 rounded border border-gray-300">
                                  {comm.vendor_name}
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-gray-500">
                              {new Date(comm.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          
                          {/* Subject for emails */}
                          {comm.subject && (
                            <p className="text-sm font-semibold text-gray-900 mb-2">
                              {comm.subject}
                            </p>
                          )}
                          
                          {/* Message Preview/Full */}
                          <div className={`text-sm text-gray-800 mb-2 ${isExpanded ? '' : 'line-clamp-2'}`}>
                            {isExpanded ? (
                              <div>
                                {comm.channel === 'phone' ? (
                                  <div className="bg-gray-50 rounded p-3 border border-gray-200">
                                    <div className="flex items-center mb-2">
                                      <Phone className="h-4 w-4 mr-2 text-blue-600" />
                                      <span className="font-semibold text-gray-900">Call Transcript</span>
                                    </div>
                                    <pre className="whitespace-pre-wrap font-sans text-sm">{comm.message}</pre>
                                  </div>
                                ) : (
                                  <pre className="whitespace-pre-wrap font-sans">{comm.message}</pre>
                                )}
                              </div>
                            ) : (
                              <p>{comm.message}</p>
                            )}
                          </div>
                          
                          {/* Metadata */}
                          <div className="flex items-center justify-between text-xs text-gray-600 pt-2 border-t border-gray-200">
                            <span>
                              {format(new Date(comm.timestamp), 'MMM d, h:mm a')}
                            </span>
                            {comm.sent_successfully ? (
                              <span className="text-green-600 flex items-center">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Delivered
                              </span>
                            ) : (
                              <span className="text-red-600">Failed</span>
                            )}
                          </div>
                          
                          {/* AI Model Used */}
                          {comm.ai_model_used && isExpanded && (
                            <div className="mt-2 pt-2 border-t border-gray-200">
                              <p className="text-xs text-gray-500">
                                Generated by: {comm.ai_model_used}
                              </p>
                            </div>
                          )}
                        </div>
                                )
                              })}
                          </div>
                        </>
                      )
                    }
                    return null
                  })()}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Request Quote Modal */}
      <RequestQuoteModal
        isOpen={requestQuoteModal.isOpen}
        onClose={() => setRequestQuoteModal({ isOpen: false, quoteIds: [], vendorNames: [] })}
        quoteIds={requestQuoteModal.quoteIds}
        vendorNames={requestQuoteModal.vendorNames}
        onRequestReal={handleRealQuoteRequest}
        onUpdate={loadWorkOrderData}
        currencySymbol={workOrder?.currency_symbol || '$'}
      />

      {/* Automation Timeline Modal */}
      {showAutomation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="max-w-6xl w-full my-8">
            <div className="relative">
              <button
                onClick={() => setShowAutomation(false)}
                className="absolute -top-4 -right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 z-10"
              >
                <span className="text-2xl">×</span>
              </button>
              <AutomationTimeline
                workOrderId={workOrderId}
                onComplete={handleAutomationComplete}
                onError={handleAutomationError}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
