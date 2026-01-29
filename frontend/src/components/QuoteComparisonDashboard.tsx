'use client'

import { Quote } from '@/lib/types'
import { Check, X, Calendar, DollarSign, Star, TrendingUp, Award } from 'lucide-react'
import { useMemo } from 'react'

interface QuoteComparisonDashboardProps {
  quotes: Quote[]
  currencySymbol?: string
  onSelectVendor: (quoteId: string) => void
  isVendorSelected?: boolean  // Whether vendor has already been selected
}

export default function QuoteComparisonDashboard({
  quotes,
  currencySymbol = '$',
  onSelectVendor,
  isVendorSelected = false
}: QuoteComparisonDashboardProps) {
  // Show all quotes with prices (including accepted/received/dispatched)
  const receivedQuotes = quotes.filter(q => q.price)

  // Calculate statistics
  const stats = useMemo(() => {
    if (receivedQuotes.length === 0) return null

    const prices = receivedQuotes.map(q => q.price!).filter(Boolean)
    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)

    return { avgPrice, minPrice, maxPrice, count: receivedQuotes.length }
  }, [receivedQuotes])

  if (receivedQuotes.length === 0) {
    return null
  }

  // Get best value using composite score (considers price + quality + availability)
  const bestValue = receivedQuotes.length > 0 ? receivedQuotes.reduce((best, current) => {
    const bestComposite = best.composite_score || 0
    const currentComposite = current.composite_score || 0
    return currentComposite > bestComposite ? current : best
  }) : null

  // Get highest rated
  const highestRated = receivedQuotes.length > 0 ? receivedQuotes.reduce((best, current) => {
    const currentScore = (current as any).vendor?.composite_score || 0
    const bestScore = (best as any).vendor?.composite_score || 0
    return currentScore > bestScore ? current : best
  }) : null

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Quote Comparison</h2>
          <p className="text-sm text-gray-600 mt-1">
            {stats?.count} quotes received • {isVendorSelected ? 'Review your selection' : 'Compare and select the best vendor'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-green-500" />
          <span className="text-sm font-medium text-gray-700">
            Ready to compare
          </span>
        </div>
      </div>

      {/* AI Recommendation - Show at top, before comparison */}
      {!isVendorSelected && bestValue && (
        <div className="mb-6 bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-300 rounded-lg p-5">
          <h4 className="font-bold text-blue-900 mb-2 flex items-center text-lg">
            <TrendingUp className="h-5 w-5 mr-2" />
            🤖 AI Recommendation
          </h4>
          <p className="text-sm text-blue-900 leading-relaxed">
            We recommend <strong>{((bestValue as any).vendor?.business_name)}</strong> at{' '}
            <strong className="text-green-700">{currencySymbol}{bestValue.price?.toFixed(2)}</strong>.{' '}
            {(() => {
              const days = bestValue.availability_date 
                ? Math.ceil((new Date(bestValue.availability_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                : null
              const rating = ((bestValue as any).vendor?.composite_score || 0).toFixed(1)
              
              return `They offer the best balance: excellent ${rating}/10 rating${days ? `, fastest availability (${days} days)` : ''}, and competitive pricing. This vendor provides optimal value across all criteria.`
            })()}
          </p>
        </div>
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Lowest Quote</p>
                <p className="text-2xl font-bold text-green-700">
                  {currencySymbol}{stats.minPrice.toFixed(2)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium">Average Quote</p>
                <p className="text-2xl font-bold text-blue-700">
                  {currencySymbol}{stats.avgPrice.toFixed(2)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600 font-medium">Highest Quote</p>
                <p className="text-2xl font-bold text-amber-700">
                  {currencySymbol}{stats.maxPrice.toFixed(2)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-amber-500" />
            </div>
          </div>
        </div>
      )}

      {/* Visual Price Comparison */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Price Comparison</h3>
        <div className="space-y-3">
          {receivedQuotes
            .sort((a, b) => (a.price || 0) - (b.price || 0))
            .map((quote, index) => {
              const vendor = (quote as any).vendor
              const percentage = stats ? ((quote.price! / stats.maxPrice) * 100) : 100
              const isBest = bestValue && quote.id === bestValue.id

              return (
                <div key={quote.id} className={`relative ${isBest ? 'ring-2 ring-green-500 rounded-lg' : ''}`}>
                  {isBest && (
                    <div className="absolute -top-2 -right-2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-full flex items-center">
                      <Award className="h-3 w-3 mr-1" />
                      BEST DEAL
                    </div>
                  )}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <div className="bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm border-2 border-gray-400 text-gray-900">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{vendor?.business_name || 'Vendor'}</p>
                          <div className="flex items-center space-x-2 text-sm text-gray-600">
                            {vendor?.composite_score && (
                              <span className="flex items-center">
                                <Star className="h-3 w-3 text-yellow-500 mr-1" />
                                {vendor.composite_score.toFixed(1)}/10
                              </span>
                            )}
                            {vendor?.price_level && (
                              <span className="text-gray-500">{vendor.price_level}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-gray-900">
                          {currencySymbol}{quote.price?.toFixed(2)}
                        </p>
                        {quote.availability_date && (
                          <p className="text-xs text-gray-600 flex items-center justify-end mt-1">
                            <Calendar className="h-3 w-3 mr-1" />
                            Available: {new Date(quote.availability_date).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {/* Action Button or Selected Badge */}
                    {isVendorSelected ? (
                      <div className="w-full mt-3 py-2 rounded-lg font-semibold text-center bg-gray-100 text-gray-600 border-2 border-gray-300">
                        {quote.status === 'accepted' ? '✓ Selected' : 'Not Selected'}
                      </div>
                    ) : (
                      <button
                        onClick={() => onSelectVendor(quote.id)}
                        className={`w-full mt-3 py-2 rounded-lg font-semibold transition-colors ${
                          isBest
                            ? 'bg-green-600 hover:bg-green-700 text-white'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'
                        }`}
                      >
                        {isBest ? '🏆 Confirm Best Deal' : 'Confirm This Vendor'}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
        </div>
      </div>

      {/* Detailed Comparison Table */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Detailed Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border">Vendor</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border">Price</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border">Rating</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border">Availability</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border">Price Range</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border">Recommended</th>
              </tr>
            </thead>
            <tbody>
              {receivedQuotes
                .sort((a, b) => (a.price || 0) - (b.price || 0))
                .map((quote) => {
                      const vendor = (quote as any).vendor
                      const isBest = bestValue && quote.id === bestValue.id
                      const isHighestRated = highestRated && quote.id === highestRated.id

                  return (
                    <tr key={quote.id} className={`${isBest ? 'bg-green-50' : 'hover:bg-gray-50'} transition-colors`}>
                      <td className="px-4 py-3 border">
                        <div className="font-medium text-gray-900">{vendor?.business_name || 'Vendor'}</div>
                        <div className="text-xs text-gray-500">{vendor?.phone || 'N/A'}</div>
                      </td>
                      <td className="px-4 py-3 border">
                        <div className="font-bold text-gray-900">
                          {currencySymbol}{quote.price?.toFixed(2)}
                        </div>
                      </td>
                      <td className="px-4 py-3 border">
                        <div className="flex items-center">
                          <Star className="h-4 w-4 text-yellow-500 mr-1" />
                          <span className="font-semibold text-gray-900">{vendor?.composite_score?.toFixed(1) || 'N/A'}</span>
                          <span className="text-gray-600 text-sm font-medium">/10</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 border">
                        <div className="text-sm text-gray-700">
                          {quote.availability_date 
                            ? new Date(quote.availability_date).toLocaleDateString()
                            : 'TBD'}
                        </div>
                      </td>
                      <td className="px-4 py-3 border">
                        <div className="text-sm text-gray-700">
                          {vendor?.price_level || 'N/A'}
                        </div>
                      </td>
                      <td className="px-4 py-3 border">
                        <div className="flex items-center space-x-1">
                          {isBest && (
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full flex items-center">
                              <Check className="h-3 w-3 mr-1" />
                              Best Deal
                            </span>
                          )}
                          {isHighestRated && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full flex items-center">
                              <Star className="h-3 w-3 mr-1" />
                              Top Rated
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
