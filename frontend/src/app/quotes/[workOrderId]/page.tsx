'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, MessageSquare, TrendingDown, Award, Clock } from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'
import QuoteComparisonDashboard from '@/components/QuoteComparisonDashboard'
import VendorConfirmationModal from '@/components/VendorConfirmationModal'

export default function QuoteComparisonPage() {
  const router = useRouter()
  const params = useParams()
  const workOrderId = params.workOrderId as string

  const [workOrder, setWorkOrder] = useState<any>(null)
  const [quotes, setQuotes] = useState<any[]>([])
  const [communications, setCommunications] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedComm, setExpandedComm] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [workOrderId])

  const loadData = async () => {
    try {
      const [woData, quotesData, commsData] = await Promise.all([
        api.getWorkOrder(workOrderId),
        api.getQuotesForWorkOrder(workOrderId),
        api.getCommunicationsForWorkOrder(workOrderId)
      ])

      setWorkOrder(woData)
      setQuotes(quotesData.quotes || [])
      setCommunications(commsData || [])
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load quote comparison')
    } finally {
      setLoading(false)
    }
  }

  const [confirmationModalOpen, setConfirmationModalOpen] = useState(false)
  const [selectedQuoteForConfirmation, setSelectedQuoteForConfirmation] = useState<any>(null)

  const handleSelectVendor = async (quoteId: string) => {
    const quote = receivedQuotes.find(q => q.id === quoteId)
    setSelectedQuoteForConfirmation(quote)
    setConfirmationModalOpen(true)
  }

  // Show all quotes with prices (including accepted/received quotes)
  const receivedQuotes = quotes.filter(q => q.price)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!workOrder) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600">Work order not found</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 text-blue-600 hover:text-blue-700"
          >
            Go back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push(`/work-orders/${workOrderId}`)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="h-5 w-5 text-gray-900" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Quote Comparison
                </h1>
                <p className="text-sm text-gray-600">
                  {workOrder.description}
                </p>
              </div>
            </div>
            <div className="text-sm">
              <span className="text-gray-600">Status:</span>{' '}
              <span className="font-semibold text-blue-600 capitalize">
                {workOrder.status.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Quote Comparison Dashboard */}
          <div className="lg:col-span-2 space-y-6">
            {/* Statistics Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Quotes</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {receivedQuotes.length}
                    </p>
                  </div>
                  <MessageSquare className="h-8 w-8 text-blue-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Best Price</p>
                    <p className="text-2xl font-bold text-green-600">
                      {receivedQuotes.length > 0
                        ? `${workOrder.currency_symbol}${Math.min(...receivedQuotes.map(q => q.price))}`
                        : 'N/A'}
                    </p>
                  </div>
                  <TrendingDown className="h-8 w-8 text-green-500" />
                </div>
              </div>
            </div>

            {/* Quote Comparison Dashboard */}
            {receivedQuotes.length > 0 ? (
              <QuoteComparisonDashboard 
                quotes={receivedQuotes}
                currencySymbol={workOrder.currency_symbol}
                onSelectVendor={handleSelectVendor}
                isVendorSelected={workOrder.status === 'dispatched' || workOrder.status === 'completed'}
              />
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <Award className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No Quotes Received Yet
                </h3>
                <p className="text-gray-600 mb-4">
                  Quotes will appear here once vendors respond
                </p>
                <button
                  onClick={() => router.push(`/work-orders/${workOrderId}`)}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  Go back to request quotes
                </button>
              </div>
            )}
          </div>

          {/* Right Column - Communication Stream */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow sticky top-24">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  Communication Stream
                </h2>
                <p className="text-xs text-gray-500 mt-1">
                  All conversations with vendors
                </p>
              </div>

              <div className="p-4 max-h-[calc(100vh-200px)] overflow-y-auto">
                {communications.length === 0 ? (
                  <div className="text-center py-8">
                    <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                    <p className="text-gray-500 text-sm">No messages yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {communications
                      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                      .map((comm) => {
                        const isExpanded = expandedComm === comm.id
                        const isOutbound = comm.direction === 'outbound'

                        return (
                          <div
                            key={comm.id}
                            className={`border-l-4 ${
                              isOutbound ? 'border-blue-500 bg-blue-50' : 'border-green-500 bg-green-50'
                            } rounded-r-lg p-3 cursor-pointer hover:shadow-md transition-shadow`}
                            onClick={() => setExpandedComm(isExpanded ? null : comm.id)}
                          >
                            <div className="flex items-start justify-between mb-1">
                              <div className="flex items-center space-x-2 flex-wrap">
                                <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full font-bold border border-blue-700">
                                  {comm.channel.toUpperCase()}
                                </span>
                                <span className={`text-xs font-semibold ${
                                  isOutbound ? 'text-blue-700' : 'text-green-700'
                                }`}>
                                  {(() => {
                                    const isFacilityManager = comm.metadata?.type === 'facility_confirmation'
                                    if (isFacilityManager) {
                                      return isOutbound ? '→ TO Manager' : '← FROM Manager'
                                    }
                                    return isOutbound 
                                      ? `→ TO ${comm.vendor_name || 'Vendor'}` 
                                      : `← FROM ${comm.vendor_name || 'Vendor'}`
                                  })()}
                                </span>
                              </div>
                              <span className="text-xs text-gray-500">
                                {new Date(comm.timestamp).toLocaleTimeString()}
                              </span>
                            </div>

                            <p className={`text-sm ${
                              isExpanded ? '' : 'line-clamp-2'
                            } ${isOutbound ? 'text-blue-900' : 'text-green-900'}`}>
                              {comm.message || comm.content}
                            </p>

                            {!isExpanded && (comm.message?.length > 100 || comm.content?.length > 100) && (
                              <p className="text-xs text-gray-500 mt-1">Click to read more...</p>
                            )}
                          </div>
                        )
                      })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Vendor Confirmation Modal */}
      {selectedQuoteForConfirmation && (
        <VendorConfirmationModal
          isOpen={confirmationModalOpen}
          onClose={() => {
            setConfirmationModalOpen(false)
            setSelectedQuoteForConfirmation(null)
          }}
          quoteId={selectedQuoteForConfirmation.id}
          vendorName={selectedQuoteForConfirmation.vendor?.business_name || 'Vendor'}
          workOrderId={workOrderId}
          onUpdate={loadData}
          quote={selectedQuoteForConfirmation}
          workOrder={workOrder}
        />
      )}
    </div>
  )
}
