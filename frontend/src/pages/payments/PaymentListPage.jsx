import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import {
  HiOutlineCreditCard,
  HiOutlinePlus,
  HiOutlineDocumentArrowDown,
  HiOutlineCurrencyDollar,
  HiOutlineCheckCircle,
} from 'react-icons/hi2';
import DataTable from '../../components/tables/DataTable';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Select from '../../components/common/Select';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import { ROLES, PAYMENT_METHODS } from '../../utils/constants';

export default function PaymentListPage() {
  const { role } = useSelector((state) => state.auth);

  const [payments, setPayments] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Record Payment Modal
  const [isRecordOpen, setIsRecordOpen] = useState(false);
  const [enrollments, setEnrollments] = useState([]);
  const [paymentForm, setPaymentForm] = useState({
    enrollment_id: '',
    amount_paid: '',
    payment_method: 'card',
    transaction_ref: '',
    notes: '',
  });
  const [recordLoading, setRecordLoading] = useState(false);
  const [recordError, setRecordError] = useState('');

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (statusFilter) params.append('status', statusFilter);

      const res = await api.get(`/api/payments?${params.toString()}`);
      setPayments(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, [page, statusFilter]);

  const handleOpenRecord = async () => {
    try {
      const res = await api.get('/api/enrollments?page=1&page_size=100&status=active');
      setEnrollments(res.data.items || []);
      setIsRecordOpen(true);
      setRecordError('');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!paymentForm.enrollment_id || !paymentForm.amount_paid) return;

    setRecordLoading(true);
    setRecordError('');
    try {
      await api.post('/api/payments', {
        enrollment_id: parseInt(paymentForm.enrollment_id),
        amount_paid: String(paymentForm.amount_paid),
        payment_method: paymentForm.payment_method,
        transaction_ref: paymentForm.transaction_ref || undefined,
        notes: paymentForm.notes || undefined,
      });
      toast.success('Payment installment recorded successfully!');
      setIsRecordOpen(false);
      setPaymentForm({
        enrollment_id: '',
        amount_paid: '',
        payment_method: 'card',
        transaction_ref: '',
        notes: '',
      });
      fetchPayments();
    } catch (err) {
      setRecordError(getApiErrorMessage(err));
    } finally {
      setRecordLoading(false);
    }
  };

  const handleDownloadReceipt = (paymentId) => {
    window.open(`${api.defaults.baseURL}/api/payments/${paymentId}/receipt`, '_blank');
  };

  const columns = [
    {
      header: 'Receipt #',
      key: 'receipt_number',
      render: (num) => (
        <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-md">
          {num}
        </span>
      ),
    },
    {
      header: 'Student & Course',
      key: 'student_name',
      render: (sName, row) => (
        <div>
          <p className="font-semibold text-slate-900 text-xs">{sName || `Student #${row.student_id}`}</p>
          <p className="text-[11px] text-slate-500">{row.course_name || `Course #${row.course_id}`}</p>
        </div>
      ),
    },
    {
      header: 'Amount Paid',
      key: 'amount_paid',
      render: (amt) => (
        <span className="font-bold text-emerald-700 text-xs">{formatCurrency(amt)}</span>
      ),
    },
    {
      header: 'Balance Left',
      key: 'pending_amount',
      render: (bal) => (
        <span className={`text-xs font-semibold ${parseFloat(bal) > 0 ? 'text-rose-600' : 'text-slate-500'}`}>
          {formatCurrency(bal)}
        </span>
      ),
    },
    {
      header: 'Method',
      key: 'payment_method',
      render: (method) => <span className="text-xs uppercase font-medium text-slate-600">{method}</span>,
    },
    {
      header: 'Status',
      key: 'status',
      render: (status) => <Badge status={status} />,
    },
    {
      header: 'Payment Date',
      key: 'payment_date',
      render: (date) => <span className="text-xs text-slate-500">{formatDateTime(date)}</span>,
    },
    {
      header: 'Receipt',
      key: 'actions',
      align: 'right',
      render: (_, row) => (
        <Button
          size="sm"
          variant="secondary"
          icon={HiOutlineDocumentArrowDown}
          onClick={() => handleDownloadReceipt(row.id)}
        >
          PDF Receipt
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Fee Payments & Receipts</h1>
          <p className="text-xs text-slate-500 mt-0.5">Track installment collections, outstanding fee balances, and PDF invoices</p>
        </div>
        {role === ROLES.ADMIN && (
          <Button variant="primary" icon={HiOutlinePlus} onClick={handleOpenRecord}>
            Record Tuition Payment
          </Button>
        )}
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex justify-end">
        <Select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          placeholder="All Payment Statuses"
          options={[
            { value: 'paid', label: 'Paid in Full' },
            { value: 'partially_paid', label: 'Partially Paid' },
            { value: 'pending', label: 'Pending' },
            { value: 'refunded', label: 'Refunded' },
          ]}
          className="w-48"
        />
      </div>

      <DataTable
        columns={columns}
        data={payments}
        isLoading={loading}
        emptyMessage="No payment records found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Record Payment Modal */}
      <Modal
        isOpen={isRecordOpen}
        onClose={() => setIsRecordOpen(false)}
        title="Record Tuition Fee Installment"
        subtitle="Applies payment against student enrollment (Prevents overpayment)"
      >
        <ErrorAlert message={recordError} onClose={() => setRecordError('')} />
        <form onSubmit={handleRecordPayment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Active Enrollment *
            </label>
            <select
              value={paymentForm.enrollment_id}
              onChange={(e) => setPaymentForm({ ...paymentForm, enrollment_id: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              <option value="">Choose an enrollment...</option>
              {enrollments.map((enr) => (
                <option key={enr.id} value={enr.id}>
                  #{enr.id} - {enr.student_name} ({enr.course_name})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Amount Paid ($) *"
              type="number"
              step="0.01"
              min="0.01"
              value={paymentForm.amount_paid}
              onChange={(e) => setPaymentForm({ ...paymentForm, amount_paid: e.target.value })}
              placeholder="0.00"
              required
            />
            <Select
              label="Payment Method *"
              value={paymentForm.payment_method}
              onChange={(e) => setPaymentForm({ ...paymentForm, payment_method: e.target.value })}
              options={PAYMENT_METHODS}
              required
            />
          </div>

          <Input
            label="Transaction Reference / Cheque #"
            value={paymentForm.transaction_ref}
            onChange={(e) => setPaymentForm({ ...paymentForm, transaction_ref: e.target.value })}
            placeholder="e.g. TXN-94829103"
          />

          <Input
            label="Internal Notes"
            value={paymentForm.notes}
            onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}
            placeholder="e.g. First semester installment"
          />

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsRecordOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={recordLoading}>
              Record Payment
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
