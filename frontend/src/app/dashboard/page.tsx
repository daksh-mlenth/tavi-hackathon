'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { Building2, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const router = useRouter()
  const [workOrders, setWorkOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadWorkOrders()
  }, [])

  const loadWorkOrders = async () => {
    try {
      const data = await api.listWorkOrders()
      setWorkOrders(data.work_orders || [])
    } catch (error) {
      console.error('Failed to load work orders:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleMarkComplete = async (workOrderId: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent navigation to detail page
    
    try {
      await api.updateWorkOrderStatus(workOrderId, 'completed')
      
      // Update local state
      setWorkOrders(prev => prev.map(wo => 
        wo.id === workOrderId 
          ? { ...wo, status: 'completed' }
          : wo
      ))
      
      // Show success toast (you'll need to add react-hot-toast)
      toast.success('✅ Work order marked as complete!')
    } catch (error) {
      console.error('Failed to mark as complete:', error)
      toast.error('Failed to mark work order as complete')
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      submitted: 'bg-gray-100 text-gray-800',
      discovering_vendors: 'bg-blue-100 text-blue-800',
      contacting_vendors: 'bg-purple-100 text-purple-800',
      evaluating_quotes: 'bg-yellow-100 text-yellow-800',
      awaiting_approval: 'bg-orange-100 text-orange-800',
      dispatched: 'bg-green-100 text-green-800',
      in_progress: 'bg-cyan-100 text-cyan-800',
      completed: 'bg-emerald-100 text-emerald-800',
      cancelled: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle className="h-5 w-5" />
    if (status === 'cancelled') return <AlertCircle className="h-5 w-5" />
    return <Clock className="h-5 w-5" />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Building2 className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Tavi Dashboard</h1>
                <p className="text-sm text-gray-500">Command Center</p>
              </div>
            </div>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
            >
              New Work Order
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Orders</p>
                <p className="text-2xl font-bold text-gray-900">{workOrders.length}</p>
              </div>
              <Building2 className="h-10 w-10 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold text-gray-900">
                  {workOrders.filter(wo => 
                    ['discovering_vendors', 'contacting_vendors', 'evaluating_quotes'].includes(wo.status)
                  ).length}
                </p>
              </div>
              <Clock className="h-10 w-10 text-yellow-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Dispatched</p>
                <p className="text-2xl font-bold text-gray-900">
                  {workOrders.filter(wo => wo.status === 'dispatched').length}
                </p>
              </div>
              <CheckCircle className="h-10 w-10 text-green-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {workOrders.filter(wo => wo.status === 'completed').length}
                </p>
              </div>
              <CheckCircle className="h-10 w-10 text-emerald-600" />
            </div>
          </div>
        </div>

        {/* Work Orders List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">All Work Orders</h2>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : workOrders.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No work orders yet. Create your first one!</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {workOrders.map((workOrder) => (
                <div
                  key={workOrder.id}
                  onClick={() => router.push(`/work-orders/${workOrder.id}`)}
                  className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">
                          {workOrder.title}
                        </h3>
                        <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(workOrder.status)}`}>
                          {getStatusIcon(workOrder.status)}
                          <span className="ml-1">{workOrder.status.replace(/_/g, ' ')}</span>
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{workOrder.description}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span className="font-medium uppercase">{workOrder.trade_type}</span>
                        <span>{workOrder.location_address}</span>
                        <span>{format(new Date(workOrder.created_at), 'MMM d, yyyy')}</span>
                      </div>
                    </div>
                    <div className="ml-4 flex items-center space-x-2">
                      {workOrder.status === 'dispatched' && (
                        <button
                          onClick={(e) => handleMarkComplete(workOrder.id, e)}
                          className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
                        >
                          ✓ Mark Complete
                        </button>
                      )}
                      <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                        View Details →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
