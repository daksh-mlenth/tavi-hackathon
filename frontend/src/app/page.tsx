'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { WorkOrderForm } from '@/components/WorkOrderForm'
import { Building2, Zap, Phone, CheckCircle } from 'lucide-react'

export default function Home() {
  const router = useRouter()

  const handleWorkOrderCreated = (workOrderId: string) => {
    router.push(`/work-orders/${workOrderId}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Building2 className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Tavi</h1>
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              View Dashboard
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold text-gray-900 sm:text-5xl md:text-6xl mb-4">
            Get Your Service Work Done
            <span className="block text-blue-600">With AI-Powered Speed</span>
          </h2>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-600 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Simply describe what you need, and our AI will find, contact, and compare vendors for you in minutes.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-lg shadow-md p-6">
            <Zap className="h-10 w-10 text-blue-600 mb-3" />
            <h3 className="text-lg font-semibold mb-2">Natural Language</h3>
            <p className="text-gray-600">Just tell us what you need in plain English</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <Phone className="h-10 w-10 text-blue-600 mb-3" />
            <h3 className="text-lg font-semibold mb-2">AI Contacts Vendors</h3>
            <p className="text-gray-600">We reach out via email, SMS, and phone automatically</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <CheckCircle className="h-10 w-10 text-blue-600 mb-3" />
            <h3 className="text-lg font-semibold mb-2">Compare & Choose</h3>
            <p className="text-gray-600">Review quotes and pick the best vendor instantly</p>
          </div>
        </div>

        {/* Work Order Form */}
        <div className="bg-white rounded-xl shadow-xl p-8 max-w-3xl mx-auto">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            Create a Work Order
          </h3>
          <WorkOrderForm onSuccess={handleWorkOrderCreated} />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center text-gray-600">
          <p>&copy; 2024 Tavi. AI-Native Service Marketplace.</p>
        </div>
      </footer>
    </div>
  )
}
