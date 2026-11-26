import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  HiOutlineClipboardDocumentList,
  HiOutlineCheckCircle,
  HiOutlineXCircle,
  HiOutlinePencilSquare,
  HiOutlineClock,
  HiOutlineEye,
} from 'react-icons/hi2';
import DataTable from '../../components/tables/DataTable';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Select from '../../components/common/Select';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDate, formatDateTime } from '../../utils/formatters';
import { ROLES, ATTENDANCE_STATUS } from '../../utils/constants';

export default function AttendancePage() {
  const [searchParams] = useSearchParams();
  const batchIdParam = searchParams.get('batch_id');
  const { role, user } = useSelector((state) => state.auth);

  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState(batchIdParam || '');
  const [selectedDate, setSelectedDate] = useState('');

  // Attendance Summary
  const [summary, setSummary] = useState(null);

  // Bulk Attendance Modal
  const [isBulkOpen, setIsBulkOpen] = useState(false);
  const [bulkBatchId, setBulkBatchId] = useState(batchIdParam || '');
  const [bulkDate, setBulkDate] = useState(new Date().toISOString().slice(0, 10));
  const [batchRoster, setBatchRoster] = useState([]);
  const [bulkEntries, setBulkEntries] = useState({});
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkError, setBulkError] = useState('');

  // Update Record Modal (with mandatory audit reason)
  const [editRecord, setEditRecord] = useState(null);
  const [editStatus, setEditStatus] = useState('present');
  const [editRemarks, setEditRemarks] = useState('');
  const [auditReason, setAuditReason] = useState('');
  const [updateLoading, setUpdateLoading] = useState(false);
  const [updateError, setUpdateError] = useState('');

  // Audit Logs Modal
  const [auditLogs, setAuditLogs] = useState([]);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        const res = await api.get('/api/batches?page=1&page_size=50');
        setBatches(res.data.items || []);
      } catch {
        // silent
      }
    };
    fetchBatches();
  }, []);

  const fetchAttendance = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (selectedBatchId) params.append('batch_id', selectedBatchId);
      if (selectedDate) params.append('session_date', selectedDate);

      const res = await api.get(`/api/attendance?${params.toString()}`);
      setRecords(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);

      // Fetch summary
      const sumParams = new URLSearchParams();
      if (selectedBatchId) sumParams.append('batch_id', selectedBatchId);
      if (role === ROLES.STUDENT && user?.id) sumParams.append('student_id', user.id);

      try {
        const sumRes = await api.get(`/api/attendance/summary?${sumParams.toString()}`);
        setSummary(sumRes.data);
      } catch {
        // silent
      }
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance();
  }, [page, selectedBatchId, selectedDate]);

  const handleOpenBulkModal = async () => {
    if (!bulkBatchId) {
      if (batches.length > 0) {
        setBulkBatchId(String(batches[0].id));
        loadRosterForBulk(batches[0].id);
      }
    } else {
      loadRosterForBulk(bulkBatchId);
    }
    setIsBulkOpen(true);
    setBulkError('');
  };

  const loadRosterForBulk = async (bId) => {
    try {
      const res = await api.get(`/api/batches/${bId}`);
      const roster = res.data.roster || [];
      setBatchRoster(roster);
      const initial = {};
      roster.forEach((st) => {
        initial[st.student_id] = { status: 'present', remarks: '' };
      });
      setBulkEntries(initial);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleBulkSubmit = async (e) => {
    e.preventDefault();
    if (!bulkBatchId || !bulkDate) return;

    setBulkLoading(true);
    setBulkError('');

    const recordsPayload = batchRoster.map((st) => ({
      student_id: st.student_id,
      status: bulkEntries[st.student_id]?.status || 'present',
      remarks: bulkEntries[st.student_id]?.remarks || undefined,
    }));

    try {
      await api.post('/api/attendance/bulk', {
        batch_id: parseInt(bulkBatchId),
        session_date: bulkDate,
        records: recordsPayload,
      });
      toast.success('Session attendance recorded in bulk!');
      setIsBulkOpen(false);
      fetchAttendance();
    } catch (err) {
      setBulkError(getApiErrorMessage(err));
    } finally {
      setBulkLoading(false);
    }
  };

  const handleUpdateRecord = async (e) => {
    e.preventDefault();
    if (!auditReason || auditReason.trim().length < 2) {
      setUpdateError('Please provide a mandatory justification reason for this audit change.');
      return;
    }
    setUpdateLoading(true);
    setUpdateError('');
    try {
      await api.put(`/api/attendance/${editRecord.id}`, {
        status: editStatus,
        remarks: editRemarks || undefined,
        reason: auditReason,
      });
      toast.success('Attendance updated with audit log entry');
      setEditRecord(null);
      fetchAttendance();
    } catch (err) {
      setUpdateError(getApiErrorMessage(err));
    } finally {
      setUpdateLoading(false);
    }
  };

  const handleViewAudit = async (recordId) => {
    try {
      const res = await api.get(`/api/attendance/${recordId}/audit-logs`);
      setAuditLogs(res.data || []);
      setIsAuditModalOpen(true);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const columns = [
    {
      header: 'Session Date',
      key: 'session_date',
      render: (date) => <span className="font-semibold text-slate-800 text-xs">{formatDate(date)}</span>,
    },
    {
      header: 'Student',
      key: 'student_name',
      render: (name, row) => (
        <div>
          <p className="font-semibold text-slate-900 text-xs">{name || `Student #${row.student_id}`}</p>
          <p className="text-[10px] text-slate-400">ID: {row.student_id}</p>
        </div>
      ),
    },
    {
      header: 'Batch Cohort',
      key: 'batch_id',
      render: (bId) => <span className="text-xs font-mono text-slate-600">Batch #{bId}</span>,
    },
    {
      header: 'Attendance Status',
      key: 'status',
      render: (status) => <Badge status={status} />,
    },
    {
      header: 'Remarks',
      key: 'remarks',
      render: (rem) => <span className="text-xs text-slate-500 italic">{rem || '-'}</span>,
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) => (
        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => handleViewAudit(row.id)}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded cursor-pointer"
            title="View Audit Trail"
          >
            <HiOutlineEye className="text-base" />
          </button>
          {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
            <Button
              size="sm"
              variant="ghost"
              icon={HiOutlinePencilSquare}
              onClick={() => {
                setEditRecord(row);
                setEditStatus(row.status);
                setEditRemarks(row.remarks || '');
                setAuditReason('');
                setUpdateError('');
              }}
            >
              Audit Edit
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Attendance Register</h1>
          <p className="text-xs text-slate-500 mt-0.5">Session tracking, audit trails, and percentage calculations</p>
        </div>
        {(role === ROLES.ADMIN || role === ROLES.INSTRUCTOR) && (
          <Button variant="primary" icon={HiOutlineClipboardDocumentList} onClick={handleOpenBulkModal}>
            Mark Session Attendance
          </Button>
        )}
      </div>

      {/* Summary KPI Card if available */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="p-4 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Attendance Rate</span>
            <p className="text-2xl font-black text-brand-600 mt-0.5">{summary.attendance_percentage}%</p>
            <span className="text-[10px] text-slate-400">Formula: P / (P + A) * 100</span>
          </Card>
          <Card className="p-4 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Classes Present</span>
            <p className="text-2xl font-black text-emerald-600 mt-0.5">{summary.present}</p>
            <span className="text-[10px] text-slate-400">Attended sessions</span>
          </Card>
          <Card className="p-4 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Classes Absent</span>
            <p className="text-2xl font-black text-rose-600 mt-0.5">{summary.absent}</p>
            <span className="text-[10px] text-slate-400">Unexcused missed classes</span>
          </Card>
          <Card className="p-4 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Eligible Sessions</span>
            <p className="text-2xl font-black text-slate-900 mt-0.5">{summary.eligible_classes}</p>
            <span className="text-[10px] text-slate-400">Excludes holidays & leaves</span>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-wrap gap-3 items-center">
        <select
          value={selectedBatchId}
          onChange={(e) => {
            setSelectedBatchId(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-300 text-xs py-2 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Batches</option>
          {batches.map((b) => (
            <option key={b.id} value={b.id}>
              {b.batch_code} - {b.name}
            </option>
          ))}
        </select>

        <Input
          type="date"
          value={selectedDate}
          onChange={(e) => {
            setSelectedDate(e.target.value);
            setPage(1);
          }}
          className="w-44 text-xs"
        />

        {(selectedBatchId || selectedDate) && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setSelectedBatchId('');
              setSelectedDate('');
            }}
          >
            Clear Filters
          </Button>
        )}
      </div>

      <DataTable
        columns={columns}
        data={records}
        isLoading={loading}
        emptyMessage="No attendance records found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Bulk Attendance Modal */}
      <Modal
        isOpen={isBulkOpen}
        onClose={() => setIsBulkOpen(false)}
        title="Mark Batch Attendance Session"
        subtitle="Record presence/absence for all students in cohort"
        maxWidth="max-w-2xl"
      >
        <ErrorAlert message={bulkError} onClose={() => setBulkError('')} />
        <form onSubmit={handleBulkSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Batch *
              </label>
              <select
                value={bulkBatchId}
                onChange={(e) => {
                  setBulkBatchId(e.target.value);
                  loadRosterForBulk(e.target.value);
                }}
                className="w-full rounded-lg border border-slate-300 text-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
                required
              >
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.batch_code} - {b.name}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Session Date *"
              type="date"
              value={bulkDate}
              onChange={(e) => setBulkDate(e.target.value)}
              required
            />
          </div>

          <div className="border border-slate-200 rounded-xl overflow-hidden max-h-72 overflow-y-auto divide-y divide-slate-100">
            {batchRoster.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">
                No students enrolled in this batch.
              </div>
            ) : (
              batchRoster.map((st) => (
                <div key={st.student_id} className="p-3 flex items-center justify-between gap-4 bg-white">
                  <div>
                    <p className="text-xs font-semibold text-slate-900">{st.full_name}</p>
                    <p className="text-[10px] font-mono text-slate-400">{st.student_code}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={bulkEntries[st.student_id]?.status || 'present'}
                      onChange={(e) => {
                        setBulkEntries({
                          ...bulkEntries,
                          [st.student_id]: {
                            ...bulkEntries[st.student_id],
                            status: e.target.value,
                          },
                        });
                      }}
                      className="rounded-lg border border-slate-300 text-xs py-1.5 px-2 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    >
                      <option value="present">Present</option>
                      <option value="absent">Absent</option>
                      <option value="approved_leave">Leave</option>
                      <option value="holiday">Holiday</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsBulkOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={bulkLoading}>
              Save Attendance Session
            </Button>
          </div>
        </form>
      </Modal>

      {/* Audit Edit Record Modal */}
      <Modal
        isOpen={!!editRecord}
        onClose={() => setEditRecord(null)}
        title="Audit Attendance Correction"
        subtitle={`Student #${editRecord?.student_id} - ${formatDate(editRecord?.session_date)}`}
      >
        <ErrorAlert message={updateError} onClose={() => setUpdateError('')} />
        <form onSubmit={handleUpdateRecord} className="space-y-4">
          <Select
            label="Corrected Attendance Status *"
            value={editStatus}
            onChange={(e) => setEditStatus(e.target.value)}
            options={[
              { value: 'present', label: 'Present' },
              { value: 'absent', label: 'Absent' },
              { value: 'approved_leave', label: 'Approved Leave' },
              { value: 'holiday', label: 'Holiday' },
              { value: 'cancelled', label: 'Cancelled' },
            ]}
          />

          <Input
            label="Optional Remarks"
            value={editRemarks}
            onChange={(e) => setEditRemarks(e.target.value)}
            placeholder="e.g. Doctor note submitted"
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Mandatory Audit Reason *
            </label>
            <textarea
              rows={2}
              value={auditReason}
              onChange={(e) => setAuditReason(e.target.value)}
              className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Why is this status being altered? (Recorded in immutable audit logs)"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setEditRecord(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={updateLoading}>
              Submit Audit Correction
            </Button>
          </div>
        </form>
      </Modal>

      {/* Audit Trail Viewer Modal */}
      <Modal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        title="Attendance Status Audit Trail"
        subtitle="Chronological log of changes and reasons"
      >
        {auditLogs.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-6">No alterations logged for this attendance record.</p>
        ) : (
          <div className="divide-y divide-slate-100 text-xs">
            {auditLogs.map((log) => (
              <div key={log.id} className="py-3 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-800">
                    {log.old_status} &rarr; <span className="text-brand-600">{log.new_status}</span>
                  </span>
                  <span className="text-[10px] text-slate-400">{formatDateTime(log.changed_at)}</span>
                </div>
                <p className="text-slate-600 italic">"{log.reason}"</p>
                <p className="text-[10px] text-slate-400">Changed by User #{log.changed_by}</p>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
}
