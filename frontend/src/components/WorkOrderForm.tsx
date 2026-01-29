'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'
import { Loader2, MessageSquare, Mic } from 'lucide-react'

interface WorkOrderFormProps {
  onSuccess?: (workOrderId: string) => void
}

export function WorkOrderForm({ onSuccess }: WorkOrderFormProps) {
  const [rawInput, setRawInput] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isListening, setIsListening] = useState(false)

  const handleVoiceInput = async () => {
    // Check if browser supports speech recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      toast.error('Speech recognition only works in Chrome or Edge browsers. Please switch browsers.')
      return
    }

    // Request microphone permission first
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      console.error('Microphone permission denied:', err)
      toast.error('Microphone access denied. Please allow microphone access in your browser settings.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setIsListening(true)
      toast.success('🎤 Listening... Speak now!')
    }

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      setRawInput((prev: string) => prev ? `${prev} ${transcript}` : transcript)
      toast.success('✅ Voice captured: "' + transcript + '"')
    }

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error)
      setIsListening(false)
      
      // Provide specific error messages
      if (event.error === 'network') {
        toast.error('Network error. Please check your internet connection.')
      } else if (event.error === 'not-allowed' || event.error === 'permission-denied') {
        toast.error('Microphone permission denied. Please allow microphone access.')
      } else if (event.error === 'no-speech') {
        toast.error('No speech detected. Please try again.')
      } else if (event.error === 'audio-capture') {
        toast.error('No microphone found. Please check your device.')
      } else if (event.error === 'aborted') {
        toast.error('Speech recognition aborted.')
      } else {
        toast.error(`Speech error: ${event.error}`)
      }
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    try {
      recognition.start()
    } catch (err) {
      console.error('Failed to start recognition:', err)
      toast.error('Failed to start voice recognition')
      setIsListening(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!rawInput.trim()) {
      toast.error('Please describe the work you need')
      return
    }

    setIsSubmitting(true)

    try {
      const response = await api.createWorkOrder({
        raw_input: rawInput,
        customer_name: customerName || undefined,
        customer_email: customerEmail || undefined,
        customer_phone: customerPhone || undefined,
      })

      toast.success('Work order created! Finding vendors...')
      
      if (onSuccess) {
        onSuccess(response.id)
      }
    } catch (error: any) {
      console.error('Error creating work order:', error)
      toast.error(error.response?.data?.detail || 'Failed to create work order')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Natural Language Input */}
      <div>
        <label htmlFor="rawInput" className="block text-sm font-medium text-gray-700 mb-2">
          Describe the work you need
        </label>
        <div className="relative">
          <textarea
            id="rawInput"
            rows={4}
            className="block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="Example: I need a plumber to fix a leaking pipe in my Dallas office at 123 Main Street. It's urgent and I'd like it done by Thursday."
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            required
          />
          <button
            type="button"
            onClick={handleVoiceInput}
            disabled={isListening}
            className={`absolute right-3 bottom-3 p-2 rounded-lg ${
              isListening 
                ? 'bg-red-100 text-red-600' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            } transition-colors`}
            title="Use voice input"
          >
            {isListening ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Mic className="h-5 w-5" />
            )}
          </button>
        </div>
        <p className="mt-2 text-sm text-gray-500">
          <MessageSquare className="inline h-4 w-4 mr-1" />
          Try using natural language! Our AI will extract all the details.
        </p>
      </div>

      {/* Optional Customer Information */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="customerName" className="block text-sm font-medium text-gray-700 mb-2">
            Your Name (Optional)
          </label>
          <input
            type="text"
            id="customerName"
            className="block w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="John Doe"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="customerEmail" className="block text-sm font-medium text-gray-700 mb-2">
            Email (Optional)
          </label>
          <input
            type="email"
            id="customerEmail"
            className="block w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="john@example.com"
            value={customerEmail}
            onChange={(e) => setCustomerEmail(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="customerPhone" className="block text-sm font-medium text-gray-700 mb-2">
            Phone (Optional)
          </label>
          <input
            type="tel"
            id="customerPhone"
            className="block w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="+1-555-0123"
            value={customerPhone}
            onChange={(e) => setCustomerPhone(e.target.value)}
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full flex justify-center items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="animate-spin h-5 w-5 mr-2" />
            Creating Work Order...
          </>
        ) : (
          'Submit Work Order'
        )}
      </button>
    </form>
  )
}
