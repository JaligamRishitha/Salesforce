import { useEffect, useState } from 'react';
import { ArrowPathIcon, CheckCircleIcon, ExclamationTriangleIcon, ClockIcon } from '@heroicons/react/24/outline';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function ServiceNowTracking() {
  const [activeTab, setActiveTab] = useState('appointments');
  const [appointments, setAppointments] = useState([]);
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'appointments') {
        const response = await api.get('/api/service/scheduling-requests');
        setAppointments(response.data);
      } else {
        const response = await api.get('/api/service/workorder-requests');
        setWorkOrders(response.data);
      }
      toast.success('Data refreshed');
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'AGENT_APPROVED':
        return 'bg-green-50 border-green-200 text-green-700';
      case 'PENDING_AGENT_REVIEW':
        return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      case 'AGENT_REJECTED':
        return 'bg-red-50 border-red-200 text-red-700';
      case 'SENT_TO_SAP':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'AGENT_APPROVED':
      case 'SENT_TO_SAP':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'PENDING_AGENT_REVIEW':
        return <ClockIcon className="w-5 h-5 text-yellow-600" />;
      case 'AGENT_REJECTED':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ServiceNow Integration Tracking</h1>
          <p className="text-sm text-gray-600">Track service appointments and work orders through ServiceNow workflow</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="btn-primary flex items-center gap-2"
        >
          <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('appointments')}
          className={`px-4 py-2 rounded-lg font-medium ${
            activeTab === 'appointments'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Service Appointments
        </button>
        <button
          onClick={() => setActiveTab('workorders')}
          className={`px-4 py-2 rounded-lg font-medium ${
            activeTab === 'workorders'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Work Orders
        </button>
      </div>

      {/* Service Appointments */}
      {activeTab === 'appointments' && (
        <div className="card">
          <div className="p-6">
            <h2 className="text-lg font-bold mb-4">Service Appointment Requests</h2>
            <div className="space-y-3">
              {appointments.length === 0 && (
                <p className="text-gray-500 text-sm">No service appointments found</p>
              )}
              {appointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className={`border rounded-lg p-4 ${getStatusColor(appointment.status)}`}
                >
                  <div className="flex items-start gap-3">
                    {getStatusIcon(appointment.status)}
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-bold">{appointment.appointment_number}</h3>
                          <p className="text-sm">Request Type: {appointment.request_type}</p>
                        </div>
                        <span className="text-xs font-bold px-2 py-1 rounded bg-white/50">
                          {appointment.status}
                        </span>
                      </div>
                      <div className="text-sm space-y-1">
                        <p><strong>ServiceNow Ticket:</strong> {appointment.mulesoft_transaction_id || 'N/A'}</p>
                        <p><strong>Integration Status:</strong> {appointment.integration_status || 'N/A'}</p>
                        {appointment.assigned_technician_id && (
                          <p><strong>Assigned Technician:</strong> {appointment.technician_name} (ID: {appointment.assigned_technician_id})</p>
                        )}
                        {appointment.error_message && (
                          <p className="text-red-600"><strong>Error:</strong> {appointment.error_message}</p>
                        )}
                        <p className="text-xs text-gray-600 mt-2">
                          Created: {new Date(appointment.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Work Orders */}
      {activeTab === 'workorders' && (
        <div className="card">
          <div className="p-6">
            <h2 className="text-lg font-bold mb-4">Work Order Requests</h2>
            <div className="space-y-3">
              {workOrders.length === 0 && (
                <p className="text-gray-500 text-sm">No work orders found</p>
              )}
              {workOrders.map((workOrder) => (
                <div
                  key={workOrder.id}
                  className={`border rounded-lg p-4 ${getStatusColor(workOrder.status)}`}
                >
                  <div className="flex items-start gap-3">
                    {getStatusIcon(workOrder.status)}
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-bold">{workOrder.work_order_number}</h3>
                          <p className="text-sm">{workOrder.subject}</p>
                        </div>
                        <span className="text-xs font-bold px-2 py-1 rounded bg-white/50">
                          {workOrder.status}
                        </span>
                      </div>
                      <div className="text-sm space-y-1">
                        <p><strong>Service Type:</strong> {workOrder.service_type}</p>
                        <p><strong>Priority:</strong> {workOrder.priority}</p>
                        <p><strong>ServiceNow Ticket:</strong> {workOrder.mulesoft_transaction_id || 'N/A'}</p>
                        <p><strong>Integration Status:</strong> {workOrder.integration_status || 'N/A'}</p>
                        <p><strong>Entitlement Verified:</strong> {workOrder.entitlement_verified ? 'Yes' : 'No'}</p>
                        {workOrder.sap_order_id && (
                          <p><strong>SAP Order ID:</strong> {workOrder.sap_order_id}</p>
                        )}
                        {workOrder.error_message && (
                          <p className="text-red-600"><strong>Error:</strong> {workOrder.error_message}</p>
                        )}
                        <p className="text-xs text-gray-600 mt-2">
                          Created: {new Date(workOrder.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Status Legend */}
      <div className="card mt-6">
        <div className="p-6">
          <h3 className="font-bold mb-3">Status Reference</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <ClockIcon className="w-4 h-4 text-yellow-600" />
              <span><strong>PENDING_AGENT_REVIEW</strong> - Waiting for agent to review in ServiceNow</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-4 h-4 text-green-600" />
              <span><strong>AGENT_APPROVED</strong> - Agent approved the request</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-4 h-4 text-blue-600" />
              <span><strong>SENT_TO_SAP</strong> - Successfully sent to SAP system</span>
            </div>
            <div className="flex items-center gap-2">
              <ExclamationTriangleIcon className="w-4 h-4 text-red-600" />
              <span><strong>AGENT_REJECTED</strong> - Agent rejected the request</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
