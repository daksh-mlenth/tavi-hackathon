'use client'
import { useEffect, useState } from 'react'
import { CheckCircle, Circle, Loader2 } from 'lucide-react'

interface TimelineStep {
  id: number
  name: string
  description: string
  icon: string
}

interface ProgressEvent {
  step: number
  status: 'in_progress' | 'completed' | 'error'
  message: string
  data?: any
  timestamp: string
}

interface AutomationTimelineProps {
  workOrderId: string
  onComplete?: () => void
  onError?: (error: string) => void
}

const STEPS: TimelineStep[] = [
  { id: 1, name: 'Discover Vendors', description: 'Finding service providers', icon: '🔍' },
  { id: 2, name: 'Request Quotes', description: 'Contacting all vendors', icon: '💬' },
  { id: 3, name: 'Collect Responses', description: 'Gathering vendor quotes', icon: '📩' },
  { id: 4, name: 'Evaluate & Select', description: 'Choosing best vendor', icon: '🎯' },
  { id: 5, name: 'Confirm & Dispatch', description: 'Final approval & dispatch', icon: '✅' }
]

export default function AutomationTimeline({ workOrderId, onComplete, onError }: AutomationTimelineProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])
  const [events, setEvents] = useState<ProgressEvent[]>([])
  const [progress, setProgress] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let eventSource: EventSource | null = null
    let isActive = true

    const startAutomation = () => {
      if (!isActive) return
      
      eventSource = new EventSource(`http://localhost:8000/api/automation/auto-handle/${workOrderId}`)

      eventSource.onmessage = (event) => {
        if (!isActive) return
        
        try {
          const data: ProgressEvent = JSON.parse(event.data)
          
          setEvents(prev => [...prev, data])

          if (data.status === 'in_progress') {
            setCurrentStep(data.step)
            if (data.data?.progress) {
              setProgress(data.data.progress)
            }
          } else if (data.status === 'completed') {
            setCompletedSteps(prev => [...prev, data.step])
            if (data.step === 5) {
              setIsComplete(true)
              eventSource?.close()
              onComplete?.()
            }
          } else if (data.status === 'error') {
            setError(data.message)
            eventSource?.close()
            onError?.(data.message)
          }
        } catch (err) {
          console.error('Failed to parse SSE event:', err)
        }
      }

      eventSource.onerror = () => {
        if (!isActive) return
        eventSource?.close()
        setError('Connection lost to automation service')
        onError?.('Connection lost')
      }
    }

    startAutomation()

    return () => {
      isActive = false
      eventSource?.close()
    }
  }, [workOrderId, onComplete, onError])

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
          <span className="mr-3">🤖</span>
          Tavi AI Agent - Autonomous Workflow
        </h2>
        <p className="text-gray-600">
          Sit back and watch AI handle everything end-to-end
        </p>
      </div>

      {/* Timeline Steps */}
      <div className="relative mb-8">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => {
            const isCompleted = completedSteps.includes(step.id)
            const isCurrent = currentStep === step.id
            const isPending = step.id > currentStep

            return (
              <div key={step.id} className="flex-1 flex flex-col items-center">
                {/* Step Circle */}
                <div className="relative z-10 mb-4">
                  <div
                    className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all duration-300 ${
                      isCompleted
                        ? 'bg-green-500 text-white shadow-lg scale-110'
                        : isCurrent
                        ? 'bg-blue-500 text-white shadow-lg scale-110 animate-pulse'
                        : 'bg-gray-200 text-gray-400'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle className="w-8 h-8" />
                    ) : isCurrent ? (
                      <Loader2 className="w-8 h-8 animate-spin" />
                    ) : (
                      step.icon
                    )}
                  </div>
                </div>

                {/* Step Info */}
                <div className="text-center">
                  <h3
                    className={`font-semibold text-sm mb-1 ${
                      isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-400'
                    }`}
                  >
                    {step.name}
                  </h3>
                  <p
                    className={`text-xs ${
                      isCompleted || isCurrent ? 'text-gray-600' : 'text-gray-400'
                    }`}
                  >
                    {step.description}
                  </p>
                </div>

                {/* Connector Line */}
                {index < STEPS.length - 1 && (
                  <div
                    className={`absolute top-8 h-1 transition-all duration-500 ${
                      completedSteps.includes(step.id)
                        ? 'bg-green-500'
                        : isCurrent
                        ? 'bg-blue-500'
                        : 'bg-gray-200'
                    }`}
                    style={{
                      left: `${((index + 1) / STEPS.length) * 100}%`,
                      width: `${(1 / STEPS.length) * 100}%`,
                      transform: 'translateX(-50%)'
                    }}
                  />
                )}
              </div>
            )
          })}
        </div>

        {/* Progress Line */}
        <div className="absolute top-8 left-0 right-0 h-1 bg-gray-200 -z-10" />
      </div>

      {/* Progress Details */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="font-semibold text-gray-900 mb-4">Live Progress</h3>
        
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {events.map((event, index) => (
            <div
              key={index}
              className={`flex items-start space-x-3 p-3 rounded-lg ${
                event.status === 'error'
                  ? 'bg-red-50 border border-red-200'
                  : event.status === 'completed'
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-blue-50 border border-blue-200'
              }`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {event.status === 'completed' ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : event.status === 'error' ? (
                  <Circle className="w-5 h-5 text-red-600" />
                ) : (
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{event.message}</p>
                {event.data?.progress && (
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${event.data.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {event.data.completed}/{event.data.total} completed ({event.data.progress}%)
                    </p>
                  </div>
                )}
              </div>
              <span className="text-xs text-gray-500">
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Completion Status */}
      {isComplete && (
        <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg p-6 text-center animate-bounce-once">
          <h3 className="text-2xl font-bold mb-2">🎉 Work Order Dispatched!</h3>
          <p className="text-green-50">
            AI successfully handled the entire workflow. Vendor is confirmed and ready to start!
          </p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-6 text-center">
          <h3 className="text-xl font-bold mb-2">❌ Error</h3>
          <p>{error}</p>
        </div>
      )}
    </div>
  )
}
