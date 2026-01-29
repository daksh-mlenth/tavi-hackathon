'use client'

import { useState } from 'react'
import { X, Send, Bot, MessageSquare, Mail, Phone } from 'lucide-react'
import VendorConversationSimulator from './VendorConversationSimulator'

interface RequestQuoteModalProps {
  isOpen: boolean
  onClose: () => void
  vendorNames: string[]
  quoteIds: string[]
  onRequestReal: () => void
  onUpdate: () => void
  currencySymbol?: string
}

export default function RequestQuoteModal({
  isOpen,
  onClose,
  vendorNames,
  quoteIds,
  onRequestReal,
  onUpdate,
  currencySymbol = '$'
}: RequestQuoteModalProps) {
  const [selectedMode, setSelectedMode] = useState<'real' | 'simulate' | null>(null)
  const [selectedQuoteForSim, setSelectedQuoteForSim] = useState<string | null>(null)

  if (!isOpen) return null

  const isSingleVendor = quoteIds.length === 1
  const vendorDisplay = isSingleVendor 
    ? vendorNames[0] 
    : `${quoteIds.length} vendors`

  const handleRealRequest = () => {
    onRequestReal()
    onClose()
  }

  if (selectedMode === 'simulate') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Bot className="h-5 w-5 mr-2 text-purple-600" />
              Simulate Conversations - {vendorDisplay}
            </h3>
            <button
              onClick={() => {
                setSelectedMode(null)
                setSelectedQuoteForSim(null)
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="p-6 space-y-4">
            {isSingleVendor ? (
              <VendorConversationSimulator
                quoteId={quoteIds[0]}
                vendorName={vendorNames[0]}
                onUpdate={onUpdate}
                currencySymbol={currencySymbol}
              />
            ) : (
              <>
                <p className="text-sm text-gray-600 mb-4">
                  Select a vendor to simulate conversation with:
                </p>
                <div className="grid gap-3">
                  {quoteIds.map((quoteId, idx) => (
                    <div key={quoteId}>
                      <button
                        onClick={() => setSelectedQuoteForSim(quoteId)}
                        className={`w-full text-left p-3 rounded-lg border-2 transition-colors ${
                          selectedQuoteForSim === quoteId
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                        }`}
                      >
                        <div className="font-medium text-gray-900">
                          {idx + 1}. {vendorNames[idx]}
                        </div>
                      </button>
                      
                      {selectedQuoteForSim === quoteId && (
                        <div className="mt-3 border-2 border-purple-200 rounded-lg">
                          <VendorConversationSimulator
                            quoteId={quoteId}
                            vendorName={vendorNames[idx]}
                            onUpdate={onUpdate}
                            currencySymbol={currencySymbol}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}

            <button
              onClick={onClose}
              className="w-full mt-4 py-2 px-4 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Request Quote
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <p className="text-sm text-gray-600 mb-6">
            How would you like to request quotes from <strong>{vendorDisplay}</strong>?
          </p>

          <div className="space-y-3">
            {/* Real Communication Option */}
            <button
              onClick={handleRealRequest}
              className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left group"
            >
              <div className="flex items-start">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                  <Send className="h-5 w-5 text-blue-600" />
                </div>
                <div className="ml-3 flex-1">
                  <div className="font-semibold text-gray-900 mb-1">
                    Send Real Communications
                  </div>
                  <div className="text-xs text-gray-600 space-y-1">
                    <div className="flex items-center">
                      <Mail className="h-3 w-3 mr-1" />
                      Email via SendGrid
                    </div>
                    <div className="flex items-center">
                      <MessageSquare className="h-3 w-3 mr-1" />
                      SMS via Twilio
                    </div>
                    <div className="flex items-center">
                      <Phone className="h-3 w-3 mr-1" />
                      Voice call via Twilio
                    </div>
                  </div>
                </div>
              </div>
            </button>

            {/* Simulation Option */}
            <button
              onClick={() => setSelectedMode('simulate')}
              className="w-full p-4 border-2 border-purple-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all text-left group"
            >
              <div className="flex items-start">
                <div className="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                  <Bot className="h-5 w-5 text-purple-600" />
                </div>
                <div className="ml-3 flex-1">
                  <div className="font-semibold text-gray-900 mb-1 flex items-center">
                    🎭 Simulate Conversations
                    <span className="ml-2 text-xs bg-purple-200 text-purple-700 px-2 py-0.5 rounded-full">
                      DEMO
                    </span>
                  </div>
                  <div className="text-xs text-gray-600">
                    Interactive demo mode - Test AI conversations with SMS, Email, and Phone transcripts
                  </div>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
