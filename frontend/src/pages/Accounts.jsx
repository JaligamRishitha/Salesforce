import { useState } from 'react';
import { BuildingOfficeIcon } from '@heroicons/react/24/solid';
import ObjectListPage from '../components/ObjectListPage';
import ImportModal from '../components/ImportModal';
import AssignLabelModal from '../components/AssignLabelModal';
import { accountsAPI } from '../services/api';
import toast from 'react-hot-toast';

const columns = [
  { key: 'name', label: 'Account Name' },
  { key: 'phone', label: 'Phone' },
  { key: 'industry', label: 'Industry' },
  { key: 'website', label: 'Website' },
  { key: 'request_status', label: 'Request Status' },
  { key: 'servicenow_ticket_id', label: 'ServiceNow Ticket' },
  { key: 'integration_status', label: 'Integration Status' },
  { key: 'correlation_id', label: 'Correlation ID' },
  { key: 'owner_alias', label: 'Account Owner Alias' },
];

export default function Accounts() {
  const [showImportModal, setShowImportModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState([]);

  const handleImport = () => {
    setShowImportModal(true);
  };

  const handleAssignLabel = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one account');
      return;
    }
    setSelectedRecords(records);
    setShowLabelModal(true);
  };

  const handleImportSuccess = () => {
    window.location.reload();
  };

  const actions = [
    {
      label: 'Import',
      onClick: handleImport,
    },
    {
      label: 'Assign Label',
      onClick: handleAssignLabel,
      requiresSelection: true,
    },
  ];

  return (
    <>
      <ObjectListPage
        objectType="account"
        objectLabel="Account"
        columns={columns}
        api={accountsAPI}
        actions={actions}
        icon={<BuildingOfficeIcon className="w-5 h-5 text-white" />}
        iconColor="bg-indigo-500"
        emptyTitle="Accounts show where your contacts work"
        emptyDescription="Improve your reporting and deal tracking with accounts."
        onSelectionChange={(ids, records) => setSelectedRecords(records)}
      />

      <ImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        objectType="account"
        api={accountsAPI}
        onSuccess={handleImportSuccess}
      />

      <AssignLabelModal
        isOpen={showLabelModal}
        onClose={() => setShowLabelModal(false)}
        selectedCount={selectedRecords.length}
        onAssign={(labels) => {
          console.log('Assigned labels:', labels);
        }}
      />
    </>
  );
}
