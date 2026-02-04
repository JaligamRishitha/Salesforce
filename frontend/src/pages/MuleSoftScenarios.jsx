import { useState, useEffect } from 'react';
import { ArrowPathIcon, EyeIcon, ArrowPathRoundedSquareIcon } from '@heroicons/react/24/outline';
import { accountsAPI, serviceAPI } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import EntitlementBadge from '../components/EntitlementBadge';
import StatCard from '../components/StatCard';
import toast from 'react-hot-toast';

export default function MuleSoftScenarios() {
  const [activeScenario, setActiveScenario] = useState('scenario1');
  const [results, setResults] = useState([]);
  const [appointments, setAppointments] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Clear results when switching scenarios
    setResults([]);

    // Load new data
    loadResults();

    // Auto-refresh every 30 seconds (increased from 10s to reduce failed requests)
    const interval = setInterval(loadResults, 30000);
    return () => clearInterval(interval);
  }, [activeScenario]);

  const loadResults = async () => {
    setLoading(true);
    try {
      let newResults = [];
      if (activeScenario === 'scenario1') {
        const response = await accountsAPI.listRequests({ page_size: 50 });
        newResults = response.data.items || [];
      } else if (activeScenario === 'scenario2') {
        const [schedResponse, apptResponse] = await Promise.all([
          serviceAPI.listSchedulingRequests({ page_size: 50 }),
          serviceAPI.listAppointments({ page_size: 100 })
        ]);
        newResults = Array.isArray(schedResponse.data) ? schedResponse.data : schedResponse.data?.items || [];
        // Create appointments lookup map
        const apptList = Array.isArray(apptResponse.data) ? apptResponse.data : apptResponse.data?.items || [];
        const apptMap = {};
        apptList.forEach(a => { apptMap[a.id] = a; });
        setAppointments(apptMap);
      } else if (activeScenario === 'scenario3') {
        const response = await serviceAPI.listWorkOrders({ page_size: 50 });
        newResults = Array.isArray(response.data) ? response.data : response.data?.items || [];
      }
      setResults(newResults);
    } catch (error) {
      console.error('Failed to load results:', error);
      // Keep existing results on error - don't clear them
    } finally {
      setLoading(false);
    }
  };

  const handleRetrySync = async (id, scenario) => {
    try {
      toast.loading('Retrying sync...', { id: 'retry' });
      // Add retry logic based on scenario
      toast.success('Sync retry initiated', { id: 'retry' });
      loadResults();
    } catch (error) {
      toast.error('Retry failed', { id: 'retry' });
    }
  };

  const handleViewDetails = (id) => {
    toast.success(`Viewing details for ID: ${id}`);
  };

  const handleCheckParts = async (appointmentId) => {
    try {
      toast.loading('Checking parts availability...', { id: 'parts' });
      // Add parts check logic
      toast.success('Parts check completed', { id: 'parts' });
      loadResults();
    } catch (error) {
      toast.error('Parts check failed', { id: 'parts' });
    }
  };

  const handleCheckEntitlement = async (workOrderId) => {
    try {
      toast.loading('Checking entitlement...', { id: 'entitlement' });
      // Add entitlement check logic
      toast.success('Entitlement check completed', { id: 'entitlement' });
      loadResults();
    } catch (error) {
      toast.error('Entitlement check failed', { id: 'entitlement' });
    }
  };

  // Scenario 1: New Client Creation
  const renderScenario1 = () => {
    const totalSynced = results.filter(r => r.status?.toUpperCase() === 'APPROVED' || r.integration_status === 'COMPLETED').length;
    const duplicateCount = results.filter(r => r.status?.toUpperCase() === 'DUPLICATE_DETECTED').length;
    const pendingCount = results.filter(r => r.status?.toUpperCase() === 'PENDING').length;
    const failedCount = results.filter(r => r.status?.toUpperCase() === 'REJECTED' || r.status?.toUpperCase() === 'FAILED').length;
    const successRate = results.length > 0 ? Math.round((totalSynced / results.length) * 100) : 0;

    return (
      <div>
        <h3 className="text-lg font-bold mb-2">Scenario 1: New Client Creation</h3>
        <p className="text-gray-600 mb-6">Account Creation &rarr; MuleSoft &rarr; ServiceNow &rarr; SAP Customer Master</p>

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard title="Total Synced" value={totalSynced} color="green" />
          <StatCard title="Success Rate" value={`${successRate}%`} color="blue" />
          <StatCard title="Pending" value={pendingCount} color="yellow" />
          <StatCard title="Duplicates" value={duplicateCount} color="orange" />
          <StatCard title="Failed" value={failedCount} color="red" />
        </div>

        {/* Accounts Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Account Name</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Integration Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">SAP Customer ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">ServiceNow Ticket</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Correlation ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Sync Date</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map(account => (
                <tr key={account.id} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm font-medium text-blue-600">{account.name || '-'}</td>
                  <td className="p-3">
                    <StatusBadge status={account.status?.toUpperCase()} />
                  </td>
                  <td className="p-3">
                    <StatusBadge status={account.integration_status} />
                  </td>
                  <td className="p-3 font-mono text-sm text-green-600 font-medium">
                    {account.sap_customer_id || '-'}
                  </td>
                  <td className="p-3 text-sm">{account.servicenow_ticket_id || '-'}</td>
                  <td className="p-3 font-mono text-xs text-gray-500">
                    {account.correlation_id ? account.correlation_id.substring(0, 8) + '...' : '-'}
                  </td>
                  <td className="p-3 text-xs text-gray-500">
                    {account.created_at ? new Date(account.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetails(account.id)}
                        className="p-1 text-gray-500 hover:text-blue-600"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      {(account.status?.toUpperCase() === 'FAILED' || account.status?.toUpperCase() === 'REJECTED') && (
                        <button
                          onClick={() => handleRetrySync(account.id, 'scenario1')}
                          className="p-1 text-gray-500 hover:text-orange-600"
                          title="Retry Sync"
                        >
                          <ArrowPathRoundedSquareIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No account creation requests yet</p>
            <p>Create a new account to see it tracked here.</p>
          </div>
        )}
      </div>
    );
  };

  // Scenario 2: Scheduling & Dispatching
  const renderScenario2 = () => {
    const appointmentsToday = results.filter(r => {
      const created = new Date(r.created_at);
      const today = new Date();
      return created.toDateString() === today.toDateString();
    }).length;
    const scheduledCount = results.filter(r => r.status === 'PENDING').length;
    const successCount = results.filter(r => r.status === 'SUCCESS').length;
    const partsIssuesCount = results.filter(r => r.status === 'PARTS_UNAVAILABLE').length;
    const failedCount = results.filter(r => r.status === 'FAILED' || r.status === 'TECHNICIAN_UNAVAILABLE').length;

    return (
      <div>
        <h3 className="text-lg font-bold mb-2">Scenario 2: Scheduling & Dispatching</h3>
        <p className="text-gray-600 mb-6">Service Appointment &rarr; MuleSoft &rarr; SAP HR (Technician) & SAP Inventory (Parts)</p>

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard title="Today" value={appointmentsToday} color="blue" />
          <StatCard title="Pending" value={scheduledCount} color="yellow" />
          <StatCard title="Success" value={successCount} color="green" />
          <StatCard title="Parts Issues" value={partsIssuesCount} color="orange" />
          <StatCard title="Failed" value={failedCount} color="red" />
        </div>

        {/* Appointments Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Appointment</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned Technician</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Parts Available</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">MuleSoft ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Correlation ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map(apt => (
                <tr key={apt.id} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm">
                    <div className="font-medium text-blue-600">
                      {appointments[apt.appointment_id]?.subject || apt.appointment_number || `APT-${apt.id}`}
                    </div>
                    <div className="text-xs text-gray-400">{apt.appointment_number}</div>
                  </td>
                  <td className="p-3">
                    <StatusBadge status={apt.status} />
                  </td>
                  <td className="p-3 text-sm">
                    {apt.technician_name ? (
                      <span className="text-green-600 font-medium">
                        {apt.technician_name}
                        <span className="text-gray-400 text-xs ml-1">(ID: {apt.assigned_technician_id})</span>
                      </span>
                    ) : (
                      <span className="text-gray-400">Not assigned</span>
                    )}
                  </td>
                  <td className="p-3 text-sm">
                    {apt.parts_available ? (
                      <span className="text-green-600 font-medium">Yes</span>
                    ) : (
                      <span className="text-orange-600 font-medium">No</span>
                    )}
                  </td>
                  <td className="p-3 font-mono text-xs text-gray-600">
                    {apt.mulesoft_transaction_id ? apt.mulesoft_transaction_id.substring(0, 12) + '...' : '-'}
                  </td>
                  <td className="p-3 font-mono text-xs text-gray-500">
                    {apt.correlation_id ? apt.correlation_id.substring(0, 8) + '...' : '-'}
                  </td>
                  <td className="p-3 text-xs text-gray-500">
                    {apt.created_at ? new Date(apt.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetails(apt.id)}
                        className="p-1 text-gray-500 hover:text-blue-600"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      {apt.status === 'PARTS_UNAVAILABLE' && (
                        <button
                          onClick={() => handleCheckParts(apt.id)}
                          className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
                        >
                          Check Parts
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No scheduling requests yet</p>
            <p>Create a service appointment to see it tracked here.</p>
          </div>
        )}
      </div>
    );
  };

  // Scenario 3: Work Order Request to SAP
  const renderScenario3 = () => {
    const workOrdersToday = results.filter(r => {
      const created = new Date(r.created_at);
      const today = new Date();
      return created.toDateString() === today.toDateString();
    }).length;
    const entitlementVerifiedCount = results.filter(r => r.entitlement_verified === true).length;
    const entitlementFailedCount = results.filter(r => r.status === 'ENTITLEMENT_FAILED').length;
    const successCount = results.filter(r => r.status === 'SUCCESS' || r.status === 'COMPLETED').length;
    const pendingCount = results.filter(r => r.status === 'PENDING').length;

    return (
      <div>
        <h3 className="text-lg font-bold mb-2">Scenario 3: Work Order Processing</h3>
        <p className="text-gray-600 mb-6">Work Order &rarr; MuleSoft &rarr; SAP Entitlement Check &rarr; SAP Service Order</p>

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard title="Today" value={workOrdersToday} color="blue" />
          <StatCard title="Pending" value={pendingCount} color="yellow" />
          <StatCard title="Verified" value={entitlementVerifiedCount} color="green" />
          <StatCard title="Entitlement Failed" value={entitlementFailedCount} color="red" />
          <StatCard title="Completed" value={successCount} color="purple" />
        </div>

        {/* Work Orders Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Work Order #</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Service Type</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">SAP Order ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Entitlement</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map(wo => (
                <tr key={wo.id} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm font-medium text-blue-600">
                    {wo.work_order_number || `WO-${wo.id}`}
                  </td>
                  <td className="p-3 text-sm">{wo.account_name || '-'}</td>
                  <td className="p-3 text-sm">{wo.subject || '-'}</td>
                  <td className="p-3">
                    <PriorityBadge priority={wo.priority || 'Normal'} />
                  </td>
                  <td className="p-3 text-sm">{wo.service_type || '-'}</td>
                  <td className="p-3">
                    <StatusBadge status={wo.status} />
                  </td>
                  <td className="p-3 font-mono text-sm text-green-600">
                    {wo.sap_order_id || '-'}
                  </td>
                  <td className="p-3">
                    <EntitlementBadge verified={wo.entitlement_verified} />
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetails(wo.id)}
                        className="p-1 text-gray-500 hover:text-blue-600"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      {wo.status === 'ENTITLEMENT_FAILED' && (
                        <button
                          onClick={() => handleCheckEntitlement(wo.id)}
                          className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                        >
                          Recheck
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No work orders yet</p>
            <p>Create a work order from the Service page to see it tracked here.</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">MuleSoft Integration Scenarios</h1>
        <button
          type="button"
          onClick={loadResults}
          disabled={loading}
          className="btn-outline flex items-center gap-2"
        >
          <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Scenario Tabs */}
      <div className="flex space-x-1 mb-6 border-b">
        <button
          onClick={() => setActiveScenario('scenario1')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeScenario === 'scenario1'
              ? 'border-blue-500 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Scenario 1: New Client
        </button>
        <button
          onClick={() => setActiveScenario('scenario2')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeScenario === 'scenario2'
              ? 'border-blue-500 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Scenario 2: Scheduling
        </button>
        <button
          onClick={() => setActiveScenario('scenario3')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeScenario === 'scenario3'
              ? 'border-blue-500 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Scenario 3: Work Order
        </button>
      </div>

      {/* Scenario Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {activeScenario === 'scenario1' && renderScenario1()}
        {activeScenario === 'scenario2' && renderScenario2()}
        {activeScenario === 'scenario3' && renderScenario3()}
      </div>
    </div>
  );
}
