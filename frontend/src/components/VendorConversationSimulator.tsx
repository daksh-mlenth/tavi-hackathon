'use client'

import { useState, useEffect } from 'react'
import { Mail, MessageSquare, Phone, Send, Sparkles, Loader2, Bot, User } from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface VendorConversationSimulatorProps {
  quoteId: string
  vendorName: string
  onUpdate: () => void
  currencySymbol?: string
}

interface Message {
  role: 'system' | 'vendor' | 'tavi'
  message: string
  channel: string
  timestamp: Date
}

export default function VendorConversationSimulator({
  quoteId,
  vendorName,
  onUpdate,
  currencySymbol = '$'
}: VendorConversationSimulatorProps) {
  const [activeChannel, setActiveChannel] = useState<'email' | 'sms' | 'phone'>('sms')
  const [message, setMessage] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [conversation, setConversation] = useState<Message[]>([])
  const [generatedTranscript, setGeneratedTranscript] = useState<string>('')
  const [isCallGenerated, setIsCallGenerated] = useState(false)

  useEffect(() => {
    generateInitialTaviMessage(activeChannel)
    setIsCallGenerated(false)
  }, [activeChannel, vendorName])

  const generateInitialTaviMessage = (channel: 'email' | 'sms' | 'phone') => {
    let initialMessage = ''
    
    if (channel === 'sms') {
      initialMessage = `Hi! This is Tavi. We have a plumbing repair job in Indore. Customer needs a leaking pipe fixed urgently by Jan 30th. Are you available? Please reply with your quote and availability. Thanks!`
    } else if (channel === 'email') {
      initialMessage = `Subject: Service Opportunity - Plumbing Repair in Indore

Dear ${vendorName},

We hope this email finds you well. We have a service opportunity that matches your expertise.

Job Details:
• Service Type: Plumbing repair
• Location: Indore, Madhya Pradesh  
• Description: Customer has a leaking pipe that needs urgent repair
• Timeline: Required by January 30th, 2026
• Urgency: High

Would you be interested in this job? Please provide:
1. Your quote for this work
2. Your availability to start
3. Estimated completion time

We review quotes from multiple vendors and will get back to you within 24 hours.

Best regards,
Tavi Team`
    } else {
      initialMessage = `[📞 This is what ${vendorName} would experience on the call...]

Click "Generate Call Transcript" below to see the full conversation!`
    }

    setConversation([{
      role: 'tavi',
      message: initialMessage,
      channel: channel,
      timestamp: new Date()
    }])
    setMessage('')
  }

  const handleSendMessage = async () => {
    if (!message.trim()) return

    try {
      setIsSending(true)
      
      // Add vendor's reply to conversation
      const vendorMessage = message
      setConversation(prev => [...prev, {
        role: 'vendor',
        message: vendorMessage,
        channel: activeChannel,
        timestamp: new Date()
      }])

      setMessage('') // Clear immediately

      // Add processing indicator
      setConversation(prev => [...prev, {
        role: 'system',
        message: '🤖 Tavi AI is processing...',
        channel: activeChannel,
        timestamp: new Date()
      }])

      // Simulate backend processing
      await api.simulateVendorReply(quoteId, vendorMessage, activeChannel)

      // Simulate thinking delay
      await new Promise(resolve => setTimeout(resolve, 1200))

      // Add Tavi AI's response back to vendor
      const taviResponse = getTaviAIResponse(vendorMessage, activeChannel)
      const isComplete = taviResponse.includes("review all quotes") || 
                         taviResponse.includes("received all the information") ||
                         taviResponse.includes("We've received everything")
      
      setConversation(prev => [
        ...prev.filter(m => m.role !== 'system'),
        {
          role: 'tavi',
          message: taviResponse,
          channel: activeChannel,
          timestamp: new Date()
        }
      ])

      if (isComplete) {
        toast.success('✅ Quote collected! Conversation complete.')
        setTimeout(() => {
          onUpdate() // Refresh quotes to show in comparison table
        }, 1000)
      } else {
        toast.success('Tavi AI responded!')
      }
    } catch (error) {
      console.error('Send error:', error)
      toast.error('Failed to send message')
    } finally {
      setIsSending(false)
    }
  }

  const handleGenerateVendorReply = async () => {
    try {
      setIsGenerating(true)
      
      if (activeChannel === 'phone') {
        await handleGenerateCallTranscript()
        return
      }
      
      await new Promise(resolve => setTimeout(resolve, 800))
      const generatedMessage = generateRealisticVendorResponse(activeChannel)
      
      console.log('Generated message:', generatedMessage)
      
      setMessage(generatedMessage)
      setIsGenerating(false)
      
      toast.success('✅ Generated! Review message above and click "Vendor Replies".')
    } catch (error) {
      console.error('Generate error:', error)
      setIsGenerating(false)
      toast.error('Failed to generate reply')
    }
  }

  const handleGenerateCallTranscript = async () => {
    try {
      const fullTranscript = generateCallTranscript()
      setGeneratedTranscript(fullTranscript)
      
      setConversation(prev => [...prev.filter(m => m.channel === 'phone'), {
        role: 'vendor',
        message: fullTranscript,
        channel: 'phone',
        timestamp: new Date()
      }])

      setIsCallGenerated(true)
      setIsGenerating(false)
      toast.success('Call transcript generated! Review and submit.')
    } catch (error) {
      setIsGenerating(false)
      toast.error('Failed to generate call')
    }
  }

  const handleSubmitCallTranscript = async () => {
    try {
      setIsSending(true)
      
      await api.simulateVendorReply(quoteId, generatedTranscript, 'phone')
      
      setConversation(prev => [...prev, {
        role: 'tavi',
        message: '✅ Call transcript processed!\n\nQuote information extracted and saved to database.',
        channel: 'phone',
        timestamp: new Date()
      }])

      setIsCallGenerated(false)
      toast.success('Quote extracted from call!')
      setTimeout(() => {
        onUpdate() // Refresh quotes to show in comparison table
      }, 1000)
    } catch (error) {
      console.error('Submit error:', error)
      toast.error('Failed to submit call')
    } finally {
      setIsSending(false)
    }
  }

  const handleRegenerateCall = () => {
    setIsCallGenerated(false)
    setGeneratedTranscript('')
    setConversation(prev => prev.filter(m => m.channel !== 'phone' || m.role === 'tavi'))
    toast('Ready to generate new call transcript')
  }

  const generateCallTranscript = (): string => {
    const prices = [150, 200, 250, 300, 350, 400, 450, 500]
    const days = [1, 2, 3, 5, 7]
    const price = prices[Math.floor(Math.random() * prices.length)]
    const availableDays = days[Math.floor(Math.random() * days.length)]
    const duration = Math.floor(Math.random() * 2) + 3

    return `[CALL TRANSCRIPT - Duration: 0:58]

[00:00] Tavi AI: Hi, calling from Tavi about a service job. Is this ${vendorName}?

[00:03] Vendor: Yes, speaking. What's the job?

[00:06] Tavi AI: We have a plumbing repair needed - leaking pipe. Are you available and interested?

[00:12] Vendor: Sure, I can do that. What's your budget and timeline?

[00:16] Tavi AI: Customer needs it within a few days. Can you provide a quote?

[00:20] Vendor: For a standard leak repair, I'd charge $${price}. Includes labor and materials.

[00:28] Tavi AI: That works. What's your availability?

[00:31] Vendor: I can start ${availableDays === 1 ? 'tomorrow' : `in ${availableDays} days`}. Takes about ${duration} hours to complete.

[00:38] Tavi AI: Perfect! To confirm - ${currencySymbol}${price}, available ${availableDays === 1 ? 'tomorrow' : `in ${availableDays} days`}, ${duration} hours?

[00:45] Vendor: Yes, that's correct. I guarantee my work.

[00:48] Tavi AI: Excellent! We'll review all quotes and contact you within 24 hours if selected.

[00:53] Vendor: Sounds good. Looking forward to it!

[00:56] Tavi AI: Thank you! Goodbye.

[00:58] [CALL ENDED]

---
[EXTRACTED INFORMATION]
• Quote: ${currencySymbol}${price}
• Availability: ${availableDays === 1 ? 'Tomorrow' : `${availableDays} days`}
• Duration: ${duration} hours`
  }

  const generateRealisticVendorResponse = (channel: 'email' | 'sms'): string => {
    const prices = [150, 200, 250, 300, 350, 400, 450, 500]
    const days = [1, 2, 3, 5, 7]
    const price = prices[Math.floor(Math.random() * prices.length)]
    const availableDays = days[Math.floor(Math.random() * days.length)]

    if (channel === 'sms') {
      const responses = [
        `Hi! I can do this for ${currencySymbol}${price}. Available in ${availableDays} days.`,
        `Sure, my quote is ${currencySymbol}${price}. Can start in ${availableDays} days. Let me know!`,
        `Yes, I'm interested. Price: ${currencySymbol}${price}. Available starting ${availableDays} days from now.`,
        `I can help. ${currencySymbol}${price} total, ready to start in ${availableDays} days.`,
      ]
      return responses[Math.floor(Math.random() * responses.length)]
    }

    return `Hi,

Thank you for reaching out! I'd be happy to help with this job.

My quote for this work is ${currencySymbol}${price}. This includes:
- All materials and labor
- Professional quality work
- 30-day warranty on workmanship

I'm available to start in ${availableDays} days and estimate completion within 1-2 days.

Please let me know if you'd like to proceed!

Best regards,
${vendorName}`
  }

  const getTaviAIResponse = (vendorMessage: string, channel: string): string => {
    const hasPrice = /\$?\d+/.test(vendorMessage)
    const hasAvailability = /\d+\s*(day|days|tomorrow|week)|available|start/i.test(vendorMessage)

    if (hasPrice && hasAvailability) {
      if (channel === 'sms') {
        return "Perfect! We've received everything we need. We'll review all quotes and contact you within 24 hours if selected. Thank you!"
      }
      return "Excellent! Thank you for providing all the details we need.\n\n✅ Quote received: Price and availability confirmed.\n\nWe'll review all vendor proposals and get back to you within 24 hours if you're selected for this job.\n\nBest regards,\nTavi Team"
    }

    if (hasPrice && !hasAvailability) {
      return channel === 'sms' 
        ? "Thanks for the quote! When can you start this work?"
        : "Thank you for the quote! That pricing looks good. Could you please let me know your availability to start the work and estimated completion time?"
    }

    if (!hasPrice && hasAvailability) {
      return channel === 'sms'
        ? "Great! What's your price quote for this job?"
        : "Excellent, that timeframe works for us! Could you provide your price quote for the complete work including materials and labor?"
    }

    return channel === 'sms'
      ? "Thanks! Please provide your price quote and availability."
      : "Thank you for your interest! To proceed, we need:\n1. Your price quote for this work\n2. Your availability to start\n\nLooking forward to your response!"
  }

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email': return <Mail className="h-4 w-4" />
      case 'sms': return <MessageSquare className="h-4 w-4" />
      case 'phone': return <Phone className="h-4 w-4" />
      default: return <MessageSquare className="h-4 w-4" />
    }
  }

  return (
    <div className="border-2 border-purple-300 rounded-lg bg-purple-50 p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-purple-900 flex items-center">
          <Bot className="h-5 w-5 mr-2" />
          🎭 Vendor Perspective: {vendorName}
        </h4>
        <div className="text-xs bg-purple-200 text-purple-700 px-2 py-1 rounded-full font-medium">
          DEMO
        </div>
      </div>

      {/* Channel Selector */}
      <div className="flex space-x-2 mb-3">
        {(['sms', 'email', 'phone'] as const).map((channel) => (
          <button
            key={channel}
            onClick={() => setActiveChannel(channel)}
            className={`flex-1 py-2 px-3 rounded-lg font-medium transition-colors flex items-center justify-center ${
              activeChannel === channel
                ? 'bg-purple-600 text-white'
                : 'bg-white text-purple-600 border border-purple-200 hover:bg-purple-100'
            }`}
          >
            {getChannelIcon(channel)}
            <span className="ml-2 capitalize">{channel}</span>
          </button>
        ))}
      </div>

      {/* Conversation Thread */}
      <div className="mb-3">
        <div className="bg-gradient-to-r from-green-100 to-blue-100 border border-green-300 rounded-t-lg px-3 py-2">
          <p className="text-sm font-semibold text-gray-800">
            📬 {vendorName}'s Inbox
          </p>
        </div>
        <div className="bg-white rounded-b-lg border-x border-b border-purple-200 p-3 max-h-96 overflow-y-auto">
          {conversation.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">
              Loading initial Tavi message...
            </p>
          ) : (
            <div className="space-y-3">
              {conversation.map((msg, idx) => {
                // Special rendering for phone call transcripts
                if (msg.channel === 'phone' && msg.role === 'vendor' && msg.message.includes('[CALL TRANSCRIPT')) {
                  return (
                    <div key={idx} className="bg-gray-50 rounded-lg p-4 border-2 border-gray-300">
                      <div className="flex items-center mb-3 pb-2 border-b border-gray-300">
                        <Phone className="h-5 w-5 mr-2 text-blue-600" />
                        <span className="font-bold text-gray-900">Full Call Transcript</span>
                        <span className="ml-auto text-xs text-gray-500">
                          {msg.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <pre className="text-xs font-mono whitespace-pre-wrap text-gray-800 leading-relaxed">
                        {msg.message}
                      </pre>
                    </div>
                  )
                }

                return (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'vendor' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg p-3 shadow-sm ${
                        msg.role === 'vendor'
                          ? 'bg-blue-500 text-white'
                          : msg.role === 'tavi'
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-700'
                      }`}
                    >
                      <div className="flex items-center mb-1">
                        {msg.role === 'vendor' ? (
                          <User className="h-3 w-3 mr-1" />
                        ) : msg.role === 'tavi' ? (
                          <Bot className="h-3 w-3 mr-1" />
                        ) : (
                          <Sparkles className="h-3 w-3 mr-1" />
                        )}
                        <span className="text-xs font-semibold">
                          {msg.role === 'vendor' ? vendorName : msg.role === 'tavi' ? 'Tavi AI' : 'System'}
                        </span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="space-y-2">
        {activeChannel === 'phone' ? (
          // Phone channel - Call generation only
          <div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
              <p className="text-sm text-blue-900 font-medium">
                ☎️ Simulate a 1-minute AI voice call with {vendorName}
              </p>
            </div>
            
            {!isCallGenerated ? (
              <button
                onClick={handleGenerateVendorReply}
                disabled={isGenerating}
                className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-bold transition-colors flex items-center justify-center disabled:opacity-50 shadow-lg"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Generating Call...
                  </>
                ) : (
                  <>
                    <Phone className="h-5 w-5 mr-2" />
                    🎙️ Generate Call Transcript
                  </>
                )}
              </button>
            ) : (
              <div className="space-y-2">
                <div className="flex space-x-2">
                  <button
                    onClick={handleRegenerateCall}
                    disabled={isSending}
                    className="flex-1 py-2 px-4 bg-white hover:bg-gray-100 text-gray-700 border-2 border-gray-300 rounded-lg font-semibold transition-colors flex items-center justify-center disabled:opacity-50"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Regenerate Call
                  </button>
                  
                  <button
                    onClick={handleSubmitCallTranscript}
                    disabled={isSending}
                    className="flex-1 py-2 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center disabled:opacity-50"
                  >
                    {isSending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-2" />
                        Submit Conversation
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-600 text-center">
                  Review the call above, regenerate if needed, or submit to extract quote
                </p>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 mb-2">
              <p className="text-xs text-blue-900 font-medium">
                ✉️ {vendorName} receives Tavi's message above. How would they reply?
              </p>
            </div>

            <textarea
              value={message}
              onChange={(e: any) => setMessage(e.target.value)}
              placeholder={`Type ${vendorName}'s ${activeChannel} response...`}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 text-sm ${
                message ? 'border-green-400 bg-green-50 text-gray-900 font-medium' : 'border-purple-200 text-gray-700'
              } ${isGenerating ? 'opacity-50' : ''}`}
              rows={activeChannel === 'email' ? 4 : 2}
              disabled={isSending || isGenerating}
            />
            
            {message && (
              <div className="text-xs text-green-600 font-medium mt-1">
                ✓ Message ready to send ({message.length} characters)
              </div>
            )}

            <div className="flex space-x-2">
              <button
                onClick={handleGenerateVendorReply}
                disabled={isSending || isGenerating}
                className="flex-1 py-2 px-4 bg-white hover:bg-purple-50 text-purple-700 border-2 border-purple-300 rounded-lg font-semibold transition-colors flex items-center justify-center disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    AI Generate Reply
                  </>
                )}
              </button>

              <button
                onClick={handleSendMessage}
                disabled={!message.trim() || isSending || isGenerating}
                className="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center disabled:opacity-50"
              >
                {isSending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Vendor Replies
                  </>
                )}
              </button>
            </div>

            <p className="text-xs text-purple-600 mt-2">
              💡 Click "AI Generate" for realistic responses, or type custom replies!
            </p>
          </>
        )}
      </div>
    </div>
  )
}
