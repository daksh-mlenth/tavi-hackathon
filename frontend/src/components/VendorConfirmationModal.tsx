'use client'
import { useState } from 'react'
import { X, Send, PlayCircle } from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface VendorConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  quoteId: string
  vendorName: string
  workOrderId: string
  onUpdate: () => void
  quote?: any 
  workOrder?: any 
}

export default function VendorConfirmationModal({
  isOpen,
  onClose,
  quoteId,
  vendorName,
  workOrderId,
  onUpdate,
  quote,
  workOrder
}: VendorConfirmationModalProps) {
  const [step, setStep] = useState<'choice' | 'simulate_facility' | 'simulate_vendor'>('choice')
  const [facilityEmail] = useState('manager@tavi.io')  // Hardcoded
  const [facilityName] = useState('Albert')  // Hardcoded
  const [taviMessageToFacility, setTaviMessageToFacility] = useState('')
  const [taviMessageToVendor, setTaviMessageToVendor] = useState('')
  const [facilityResponse, setFacilityResponse] = useState('')
  const [vendorResponse, setVendorResponse] = useState('')
  const [loading, setLoading] = useState(false)

  if (!isOpen) return null

  const handleChooseSimulate = async () => {
    setLoading(true)
    try {
      // Generate AI message from Tavi to Facility Manager
      const facilityMsg = await generateTaviMessageToFacilityManager()
      setTaviMessageToFacility(facilityMsg)
      setStep('simulate_facility')
    } catch (error) {
      console.error('Failed to generate message:', error)
      toast.error('Failed to generate message')
    } finally {
      setLoading(false)
    }
  }

  const handleSendRealConfirmations = async () => {
    setLoading(true)
    try {
      await api.confirmVendor(quoteId, facilityEmail, facilityName)
      toast.success('✅ Confirmations sent to facility manager and vendor!')
      onUpdate()
      onClose()
    } catch (error) {
      console.error('Failed to send confirmations:', error)
      toast.error('Failed to send confirmations')
    } finally {
      setLoading(false)
    }
  }

  const generateTaviMessageToFacilityManager = async () => {
    // AI-generated message requesting facility manager approval
    const messages = [
      `Dear ${facilityName},\n\nWe have completed the vendor selection process for the work order and recommend ${vendorName} based on their competitive pricing, high ratings, and availability.\n\nKey Details:\n• Vendor: ${vendorName}\n• Status: Ready for dispatch\n\nPlease review and reply with "APPROVED" to proceed with vendor dispatch, or "REJECT" if you have concerns.\n\nBest regards,\nTavi AI System`,
      
      `Hi ${facilityName},\n\nOur AI system has identified ${vendorName} as the best match for your work order based on quality, pricing, and availability metrics.\n\nWe recommend moving forward with this vendor. Please confirm by replying "APPROVED" or provide feedback if you'd like to review other options.\n\nThank you,\nTavi Team`,
      
      `Hello ${facilityName},\n\nVendor selection complete! We've chosen ${vendorName} based on:\n✓ Excellent ratings and reviews\n✓ Competitive pricing\n✓ Quick availability\n\nPlease approve this selection by responding "APPROVED" to proceed with dispatch.\n\nRegards,\nTavi AI`
    ]
    
    return messages[Math.floor(Math.random() * messages.length)]
  }

  const generateTaviMessageToVendor = async () => {
    const price = quote?.price || 'N/A'
    const currency = workOrder?.currency_symbol || '$'
    const address = workOrder?.location_address || 'Location TBD'
    const city = workOrder?.location_city || ''
    const state = workOrder?.location_state || ''
    const description = workOrder?.description || 'Work order'
    const availabilityDate = quote?.availability_date 
      ? new Date(quote.availability_date).toLocaleDateString() 
      : 'TBD'
    const estimatedDuration = quote?.estimated_duration 
      ? `${quote.estimated_duration} hours` 
      : workOrder?.estimated_hours 
        ? `${workOrder.estimated_hours} hours` 
        : 'TBD'
    
    const messages = [
      `Hi ${vendorName},

Congratulations! You have been selected for this job. 🎉

JOB DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━
📋 Work Order: ${description}
📍 Location: ${address}${city ? `, ${city}` : ''}${state ? `, ${state}` : ''}
💰 Agreed Price: ${currency}${price}
📅 Start Date: ${availabilityDate}
⏱️ Estimated Duration: ${estimatedDuration}

NEXT STEPS:
The facility manager has approved your quote. Please confirm your availability and dispatch readiness by replying "CONFIRMED".

If you have any questions about the job site, materials, or timeline, please let us know immediately.

We're looking forward to working with you!

Best regards,
Tavi Team`,
      
      `Hello ${vendorName},

Great news - you've been awarded the job!

━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT INFORMATION:
• Description: ${description}
• Service Location: ${address}${city ? `, ${city}` : ''}
• Your Quote: ${currency}${price}
• Scheduled Start: ${availabilityDate}
• Duration: ${estimatedDuration}
━━━━━━━━━━━━━━━━━━━━━━━━

The facility manager has approved this selection. Please respond with "CONFIRMED" to verify you can start on the agreed date and complete the work as quoted.

Contact us if you need any clarifications or have concerns about the timeline.

Thank you,
Tavi AI System`,
      
      `Dear ${vendorName},

Excellent news! The facility manager selected your proposal. ✓

Work Order Summary:
━━━━━━━━━━━━━━━━━━━━━━━━
${description}

Job Site: ${address}
${city && state ? `${city}, ${state}` : ''}

Contracted Amount: ${currency}${price}
Start Date: ${availabilityDate}
Estimated Time: ${estimatedDuration}
━━━━━━━━━━━━━━━━━━━━━━━━

Please confirm dispatch by replying "CONFIRMED" to acknowledge:
✓ You can arrive on ${availabilityDate}
✓ You have reviewed the job site address
✓ You're prepared to complete the work for ${currency}${price}

If you need to adjust anything, contact us ASAP.

Best,
Tavi Team`
    ]
    
    return messages[Math.floor(Math.random() * messages.length)]
  }

  const handleSimulateFacilityResponse = async (approved: boolean) => {
    if (!facilityResponse.trim()) {
      toast.error('Please enter or generate facility manager response')
      return
    }
    
    setLoading(true)
    try {
      // First, confirm the vendor (this will set up the work order status)
      await api.confirmVendor(quoteId, facilityEmail, facilityName)
      
      // Then simulate facility manager response
      await api.simulateFacilityConfirmation(workOrderId, approved)
      
      if (approved) {
        toast.success('✅ Facility Manager APPROVED!')
        // Generate Tavi's message to vendor
        const vendorMsg = await generateTaviMessageToVendor()
        setTaviMessageToVendor(vendorMsg)
        setStep('simulate_vendor')
      } else {
        toast.error('❌ Facility Manager REJECTED')
        onUpdate()
        onClose()
      }
    } catch (error) {
      console.error('Failed to simulate facility response:', error)
      toast.error('Failed to simulate facility response')
    } finally {
      setLoading(false)
    }
  }

  const handleSimulateVendorResponse = async (confirmed: boolean) => {
    if (!vendorResponse.trim()) {
      toast.error('Please enter or generate vendor response')
      return
    }
    
    setLoading(true)
    try {
      await api.simulateVendorDispatchConfirmation(workOrderId, confirmed)
      
      if (confirmed) {
        toast.success('🎉 Both confirmations complete! Vendor DISPATCHED!')
      } else {
        toast.error('❌ Vendor cannot confirm dispatch')
      }
      
      onUpdate()
      onClose()
    } catch (error) {
      console.error('Failed to simulate vendor response:', error)
      toast.error('Failed to simulate vendor response')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateFacilityResponse = () => {
    const responses = [
      "APPROVED - Vendor selection looks great! Please proceed with dispatch.",
      "APPROVED - I've reviewed the quote and vendor profile. Looks good to me!",
      "APPROVED - Yes, this vendor has worked with us before. Approve.",
    ]
    setFacilityResponse(responses[Math.floor(Math.random() * responses.length)])
  }

  const handleGenerateVendorResponse = () => {
    const responses = [
      "CONFIRMED - I'll be there on the scheduled date. Thank you!",
      "CONFIRMED - Looking forward to working with you. I can start as planned.",
      "CONFIRMED - Yes, I confirm dispatch for the agreed date and time.",
    ]
    setVendorResponse(responses[Math.floor(Math.random() * responses.length)])
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-xl">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">Confirm Vendor Selection</h2>
              <p className="text-blue-100">
                {vendorName}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6">
          {/* Step 1: Choose Real or Simulate */}
          {step === 'choice' && (
            <div className="space-y-6">
              <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
                <h3 className="font-semibold text-gray-900 mb-2">Two-Step Confirmation Required:</h3>
                <ol className="text-sm text-gray-700 space-y-1 ml-4 list-decimal">
                  <li><strong>Facility Manager</strong> must approve vendor selection</li>
                  <li><strong>Vendor</strong> must confirm dispatch availability</li>
                  <li>Both confirmations → <strong>Dispatched!</strong> ✓</li>
                </ol>
              </div>

              {/* Facility Manager Info (Hardcoded) */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Facility Manager:</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600">👤 Name:</span>
                    <span className="font-medium text-gray-900">{facilityName}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600">📧 Email:</span>
                    <span className="font-medium text-gray-900">{facilityEmail}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={handleSendRealConfirmations}
                  disabled={loading}
                  className="flex items-center justify-center space-x-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-4 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                >
                  <Send className="h-5 w-5" />
                  <span>Send Real Communications</span>
                </button>

                <button
                  onClick={handleChooseSimulate}
                  disabled={loading}
                  className="flex items-center justify-center space-x-2 bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white px-6 py-4 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                >
                  <PlayCircle className="h-5 w-5" />
                  <span>{loading ? 'Generating...' : 'Simulate Confirmations'}</span>
                </button>
              </div>

              <p className="text-xs text-gray-500 text-center">
                💡 For demo purposes, use "Simulate" to test the confirmation flow
              </p>
            </div>
          )}

          {/* Step 2: Simulate Facility Manager Response */}
          {step === 'simulate_facility' && (
            <div className="space-y-6">
              <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
                <h3 className="font-semibold text-gray-900 mb-2">
                  👔 Step 1: Facility Manager Response
                </h3>
                <p className="text-sm text-gray-700">
                  Tavi AI has sent a confirmation email to <strong>{facilityEmail}</strong>. 
                  Simulate their response:
                </p>
              </div>

              {/* Tavi's Outbound Message */}
              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-xs font-bold text-blue-700">→ FROM TAVI</span>
                  <span className="text-xs bg-blue-200 text-blue-800 px-2 py-0.5 rounded-full">EMAIL</span>
                </div>
                <div className="text-sm text-gray-800 whitespace-pre-wrap">
                  <p className="font-medium mb-2">Subject: Vendor Selection Approval Required</p>
                  {taviMessageToFacility}
                </div>
              </div>

              {/* Simulate Facility Manager Reply */}
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Facility Manager Reply:
                  </label>
                  <button
                    onClick={handleGenerateFacilityResponse}
                    className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                  >
                    🤖 AI Generate
                  </button>
                </div>
                <textarea
                  value={facilityResponse}
                  onChange={(e) => setFacilityResponse(e.target.value)}
                  placeholder="Type facility manager's response or click 'AI Generate'..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900 font-medium"
                  rows={3}
                />
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => handleSimulateFacilityResponse(false)}
                  disabled={loading}
                  className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
                >
                  ❌ Reject
                </button>
                <button
                  onClick={() => handleSimulateFacilityResponse(true)}
                  disabled={loading}
                  className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
                >
                  ✅ Approve
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Simulate Vendor Dispatch Response */}
          {step === 'simulate_vendor' && (
            <div className="space-y-6">
              <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
                <h3 className="font-semibold text-gray-900 mb-2">
                  🔧 Step 2: Vendor Dispatch Confirmation
                </h3>
                <p className="text-sm text-gray-700">
                  Facility Manager approved! ✅ Now Tavi AI is contacting <strong>{vendorName}</strong> for dispatch confirmation.
                </p>
              </div>

              {/* Tavi's Outbound Message to Vendor */}
              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-xs font-bold text-blue-700">→ FROM TAVI</span>
                  <span className="text-xs bg-blue-200 text-blue-800 px-2 py-0.5 rounded-full">SMS/EMAIL</span>
                </div>
                <div className="text-sm text-gray-800 whitespace-pre-wrap">
                  {taviMessageToVendor}
                </div>
              </div>

              {/* Simulate Vendor Reply */}
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Vendor Reply:
                  </label>
                  <button
                    onClick={handleGenerateVendorResponse}
                    className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                  >
                    🤖 AI Generate
                  </button>
                </div>
                <textarea
                  value={vendorResponse}
                  onChange={(e) => setVendorResponse(e.target.value)}
                  placeholder="Type vendor's response or click 'AI Generate'..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900 font-medium"
                  rows={3}
                />
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => handleSimulateVendorResponse(false)}
                  disabled={loading}
                  className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
                >
                  ❌ Cannot Confirm
                </button>
                <button
                  onClick={() => handleSimulateVendorResponse(true)}
                  disabled={loading}
                  className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
                >
                  ✅ Confirm Dispatch
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
