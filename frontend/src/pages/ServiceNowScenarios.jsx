import { useState, useEffect } from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon, ClockIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import api from '../services/api';

export default function ServiceNowScenarios() {
  const [activeScenario, setActiveScenario] = useState('scenario2');
  const [loading, setLoading] = useState(false);

  // Scenario 2: Service Appointment (Scheduling & Dispatching)
  const [appointmentForm, setAppointmentForm] = useState({
    case_id: '',
    account_id: '',
    subject: '',
    description: '',
    appointment_type: 'Field Service',
    scheduled_start: '',
    scheduled_end: '',
    priority: 'Normal',
    location: '',
    required_skills: '',
    required_parts: '',
  });

  // Scenario 3: Work Order
  const [workOrderForm, setWorkOrderForm] = useState({
    case_id: '',
    account_id: '',
    subject: '',
    description: '',
    priority: 'Medium',
    service_type: 'Warranty',
    product: '',
  });

  // Pending requests for agent approval
  const [pendingAppointments, setPendingAppointments] = useState([]);
  const [pendingWorkOrders, setPendingWorkOrders] = useState([]);

  const loadPendingRequests = async () => {
    try {
      if (activeScenario === 'scenario2') {
        const response = await api.get('/api/service/scheduling-requests?status=PENDING_AGENT_REVIEW');
        setPendingAppointments(response.data);
      } else if (activeScenario === 'scenario3') {
        const response = await api.get('/api/service/workorder-requests?status=PENDING_AGENT_REVIEW');
        setPendingWorkOrders(response.data);
      }
    } catch (error) {
      console.error('Failed to load pending requests:', error);
    }
  };

  useEffect(() => {
    loadPendingRequests();
  }, [activeScenario]);

  const handleAppointmentSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post('/api/service/appointments', appointmentForm);
      toast.success('Service appointment created and sent to ServiceNow for agent review');
      setAppointmentForm({
        case_id: '',
        account_id: '',
        subject: '',
        description: '',
        appointment_type: 'Field Service',
        scheduled_start: '',
        scheduled_end: '',
        priority: 'Normal',
        location: '',
        required_skills: '',
        required_parts: '',
      });
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create appointment');
    } finally {
      setLoading(false);
    }
  };

  const handleWorkOrderSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post('/api/service/work-orders', workOrderForm);
      toast.success('Work order created and sent to ServiceNow for agent review');
      setWorkOrderForm({
        case_id: '',
        account_id: '',
        subject: '',
        description: '',
        priority: 'Medium',
        service_type: 'Warranty',
        product: '',
      });
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create work order');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAppointment = async (requestId) => {
    const technicianId = prompt('Enter Technician ID:');
    const technicianName = prompt('Enter Technician Name:');

    if (!technicianId || !technicianName) {
      toast.error('Technician details are required');
      return;
    }

    try {
      await api.post(`/api/service/scheduling-requests/${requestId}/approve?technician_id=${technicianId}&technician_name=${technicianName}`);
      toast.success('Appointment approved and sent to SAP');
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve appointment');
    }
  };

  const handleRejectAppointment = async (requestId) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;

    try {
      await api.post(`/api/service/scheduling-requests/${requestId}/reject?reason=${encodeURIComponent(reason)}`);
      toast.success('Appointment rejected');
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject appointment');
    }
  };

  const handleApproveWorkOrder = async (requestId) => {
    try {
      await api.post(`/api/service/work-order-requests/${requestId}/approve?entitlement_verified=true`);
      toast.success('Work order approved and sent to SAP');
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve work order');
    }
  };

  const handleRejectWorkOrder = async (requestId) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;

    try {
      await api.post(`/api/service/work-order-requests/${requestId}/reject?reason=${encodeURIComponent(reason)}`);
      toast.success('Work order rejected');
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject work order');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">ServiceNow Integration</h1>
        <p className="text-sm text-gray-600">Salesforce → ServiceNow → Agent Review → SAP</p>
      </div>

      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveScenario('scenario2')}
          className={`px-4 py-2 rounded-lg font-medium ${
            activeScenario === 'scenario2'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Service Appointments
        </button>
        <button
          onClick={() => setActiveScenario('scenario3')}
          className={`px-4 py-2 rounded-lg font-medium ${
            activeScenario === 'scenario3'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Work Orders
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Form Section */}
        <div>
          <div className="card p-6">
            {activeScenario === 'scenario2' && (
              <form onSubmit={handleAppointmentSubmit}>
                <h2 className="text-lg font-bold mb-4">Create Service Appointment</h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="number"
                      placeholder="Case ID"
                      value={appointmentForm.case_id}
                      onChange={(e) => setAppointmentForm({ ...appointmentForm, case_id: e.target.value })}
                      className="input"
                    />
                    <input
                      type="number"
                      placeholder="Account ID"
                      value={appointmentForm.account_id}
                      onChange={(e) => setAppointmentForm({ ...appointmentForm, account_id: e.target.value })}
                      className="input"
                    />
                  </div>
                  <input
                    type="text"
                    placeholder="Subject"
                    value={appointmentForm.subject}
                    onChange={(e) => setAppointmentForm({ ...appointmentForm, subject: e.target.value })}
                    className="input"
                    required
                  />
                  <textarea
                    placeholder="Description"
                    value={appointmentForm.description}
                    onChange={(e) => setAppointmentForm({ ...appointmentForm, description: e.target.value })}
                    className="input"
                    rows="3"
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <select
                      value={appointmentForm.appointment_type}
                      onChange={(e) => setAppointmentForm({ ...appointmentForm, appointment_type: e.target.value })}
                      className="input"
                    >
                      <option>Field Service</option>
                      <option>Remote Support</option>
                      <option>On-Site Visit</option>
                    </select>
                    <select
                      value={appointmentForm.priority}
                      onChange={(e) => setAppointmentForm({ ...appointmentForm, priority: e.target.value })}
                      className="input"
                    >
                      <option>Normal</option>
                      <option>High</option>
                      <option>Urgent</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="datetime-local"
                      placeholder="Scheduled Start"
                      value={appointmentForm.scheduled_start}
                      onChange={(e) => setAppointmentForm({ ...appointmentForm, scheduled_start: e.target.value })}
                      className="input"
                    />
                    <input
                      type="datetime-local"
                      placeholder="Scheduled End"
                      value={appointmentForm.scheduled_end}
                      onChange={(e) => setAppointmentForm({ ...appointmentForm, scheduled_end: e.target.value })}
                      className="input"
                    />
                  </div>
                  <input
                    type="text"
                    placeholder="Location"
                    value={appointmentForm.location}
                    onChange={(e) => setAppointmentForm({ ...appointmentForm, location: e.target.value })}
                    className="input"
                  />
                  <input
                    type="text"
                    placeholder="Required Skills"
                    value={appointmentForm.required_skills}
                    onChange={(e) => setAppointmentForm({ ...appointmentForm, required_skills: e.target.value })}
                    className="input"
                  />
                  <input
                    type="text"
                    placeholder="Required Parts"
                    value={appointmentForm.required_parts}
                    onChange={(e) => setAppointmentForm({ ...appointmentForm, required_parts: e.target.value })}
                    className="input"
                  />
                </div>
                <button type="submit" className="btn-primary mt-4 w-full" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Appointment'}
                </button>
              </form>
            )}

            {activeScenario === 'scenario3' && (
              <form onSubmit={handleWorkOrderSubmit}>
                <h2 className="text-lg font-bold mb-4">Create Work Order</h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="number"
                      placeholder="Case ID"
                      value={workOrderForm.case_id}
                      onChange={(e) => setWorkOrderForm({ ...workOrderForm, case_id: e.target.value })}
                      className="input"
                    />
                    <input
                      type="number"
                      placeholder="Account ID"
                      value={workOrderForm.account_id}
                      onChange={(e) => setWorkOrderForm({ ...workOrderForm, account_id: e.target.value })}
                      className="input"
                    />
                  </div>
                  <input
                    type="text"
                    placeholder="Subject"
                    value={workOrderForm.subject}
                    onChange={(e) => setWorkOrderForm({ ...workOrderForm, subject: e.target.value })}
                    className="input"
                    required
                  />
                  <textarea
                    placeholder="Description"
                    value={workOrderForm.description}
                    onChange={(e) => setWorkOrderForm({ ...workOrderForm, description: e.target.value })}
                    className="input"
                    rows="3"
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <select
                      value={workOrderForm.service_type}
                      onChange={(e) => setWorkOrderForm({ ...workOrderForm, service_type: e.target.value })}
                      className="input"
                    >
                      <option>Warranty</option>
                      <option>Maintenance</option>
                      <option>Repair</option>
                      <option>Installation</option>
                    </select>
                    <select
                      value={workOrderForm.priority}
                      onChange={(e) => setWorkOrderForm({ ...workOrderForm, priority: e.target.value })}
                      className="input"
                    >
                      <option>Low</option>
                      <option>Medium</option>
                      <option>High</option>
                      <option>Critical</option>
                    </select>
                  </div>
                  <input
                    type="text"
                    placeholder="Product"
                    value={workOrderForm.product}
                    onChange={(e) => setWorkOrderForm({ ...workOrderForm, product: e.target.value })}
                    className="input"
                  />
                </div>
                <button type="submit" className="btn-primary mt-4 w-full" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Work Order'}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Pending Agent Review Section */}
        <div>
          <div className="card p-6">
            <h2 className="text-lg font-bold mb-4">Pending Agent Review</h2>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {activeScenario === 'scenario2' && pendingAppointments.length === 0 && (
                <p className="text-gray-500 text-sm">No pending appointments</p>
              )}
              {activeScenario === 'scenario2' && pendingAppointments.map((request) => (
                <div key={request.id} className="border rounded-lg p-4 bg-yellow-50">
                  <div className="flex items-start gap-2 mb-2">
                    <ClockIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-bold text-sm">{request.appointment_number}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Status: {request.status}
                      </p>
                      {request.mulesoft_transaction_id && (
                        <p className="text-xs text-gray-600">
                          ServiceNow: {request.mulesoft_transaction_id}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => handleApproveAppointment(request.id)}
                      className="flex-1 bg-green-600 text-white text-xs py-2 rounded hover:bg-green-700"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleRejectAppointment(request.id)}
                      className="flex-1 bg-red-600 text-white text-xs py-2 rounded hover:bg-red-700"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}

              {activeScenario === 'scenario3' && pendingWorkOrders.length === 0 && (
                <p className="text-gray-500 text-sm">No pending work orders</p>
              )}
              {activeScenario === 'scenario3' && pendingWorkOrders.map((workOrder) => (
                <div key={workOrder.id} className="border rounded-lg p-4 bg-yellow-50">
                  <div className="flex items-start gap-2 mb-2">
                    <ClockIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-bold text-sm">{workOrder.work_order_number}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        {workOrder.subject}
                      </p>
                      <p className="text-xs text-gray-600">
                        Status: {workOrder.status}
                      </p>
                      {workOrder.mulesoft_transaction_id && (
                        <p className="text-xs text-gray-600">
                          ServiceNow: {workOrder.mulesoft_transaction_id}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => handleApproveWorkOrder(workOrder.id)}
                      className="flex-1 bg-green-600 text-white text-xs py-2 rounded hover:bg-green-700"
                    >
                      Approve & Send to SAP
                    </button>
                    <button
                      onClick={() => handleRejectWorkOrder(workOrder.id)}
                      className="flex-1 bg-red-600 text-white text-xs py-2 rounded hover:bg-red-700"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
