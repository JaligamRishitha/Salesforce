import { useState } from 'react';
import axios from 'axios';

export default function IntegrationTracking() {
  const [correlationId, setCorrelationId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!correlationId.trim()) return;

    setLoading(true);
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/integration-tracking/${correlationId}`
      );
      setResult(response.data);
      
      // Add to search history
      if (!searchHistory.find(h => h.id === correlationId)) {
        setSearchHistory([{ id: correlationId, timestamp: new Date() }, ...searchHistory.slice(0, 9)]);
      }
    } catch (error) {
      setResult(null);
      alert('Correlation ID not found');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      SUCCESS: 'bg-green-100 text-green-800',
      DUPLICATE_DETECTED: 'bg-yellow-100 text-yellow-800',
      PARTS_UNAVAILABLE: 'bg-orange-100 text-orange-800',
      ENTITLEMENT_FAILED: 'bg-red-100 text-red-800',
      ERROR: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    const icons = {
      SUCCESS: '✅',
      DUPLICATE_DETECTED: '⚠️',
      PARTS_UNAVAILABLE: '📦',
      ENTITLEMENT_FAILED: '❌',
      ERROR: '❌'
    };
    return icons[status] || '•';
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Integration Tracking</h1>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Enter Correlation ID..."
            value={correlationId}
            onChange={(e) => setCorrelationId(e.target.value)}
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Search History */}
      {searchHistory.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-bold mb-3">Recent Searches</h3>
          <div className="flex flex-wrap gap-2">
            {searchHistory.map(item => (
              <button
                key={item.id}
                onClick={() => {
                  setCorrelationId(item.id);
                  document.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true }));
                }}
                className="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 text-sm"
              >
                {item.id.substring(0, 8)}...
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-2 gap-6">
            {/* Left Column */}
            <div>
              <h3 className="text-lg font-bold mb-4">Integration Details</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">ID</label>
                  <p className="font-mono text-sm">{result.id}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Status</label>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(result.status)}`}>
                    {getStatusIcon(result.status)} {result.status}
                  </span>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Correlation ID</label>
                  <p className="font-mono text-sm">{result.correlation_id}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Message</label>
                  <p className="text-sm">{result.message}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Created</label>
                  <p className="text-sm">{new Date(result.created_at).toLocaleString()}</p>
                </div>
              </div>
            </div>

            {/* Right Column - Scenario-specific data */}
            <div>
              <h3 className="text-lg font-bold mb-4">Integration References</h3>
              
              <div className="space-y-4">
                {/* Scenario 1 */}
                {result.sap_customer_id && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">SAP Customer ID</label>
                    <p className="font-mono text-sm bg-blue-50 p-2 rounded">{result.sap_customer_id}</p>
                  </div>
                )}

                {/* Scenario 2 */}
                {result.appointment_id && (
                  <>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Appointment ID</label>
                      <p className="font-mono text-sm bg-blue-50 p-2 rounded">{result.appointment_id}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Assigned Technician</label>
                      <p className="text-sm">{result.assigned_technician_id || '-'}</p>
                    </div>
                  </>
                )}

                {/* Scenario 3 */}
                {result.sap_order_id && (
                  <>
                    <div>
                      <label className="text-sm font-medium text-gray-600">SAP Order ID</label>
                      <p className="font-mono text-sm bg-blue-50 p-2 rounded">{result.sap_order_id}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">SAP Notification ID</label>
                      <p className="font-mono text-sm bg-blue-50 p-2 rounded">{result.sap_notification_id}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Entitlement Verified</label>
                      <span className={`inline-block px-3 py-1 rounded text-sm ${result.entitlement_verified ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {result.entitlement_verified ? '✅ Yes' : '❌ No'}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {!result && correlationId && !loading && (
        <div className="text-center py-8 text-gray-500">
          Enter a correlation ID and click Search to view integration details
        </div>
      )}
    </div>
  );
}
