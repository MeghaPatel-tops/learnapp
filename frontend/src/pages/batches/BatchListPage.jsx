import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import {
  HiOutlineUserGroup,
  HiOutlinePlus,
  HiOutlineMagnifyingGlass,
  HiOutlineCalendar,
  HiOutlineClock,
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
import { formatDate } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function BatchListPage() {
  const navigate = useNavigate();
  const { role } = useSelector((state) => state.auth);

  const [batches, setBatches] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Create Batch Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [courses, setCourses] = useState([]);
  const [instructors, setInstructors] = useState([]);
  const [createForm, setCreateForm] = useState({
    batch_code: '',
    name: '',
    course_id: '',
    instructor_id: '',
    start_date: '',
    end_date: '',
    class_days: 'Mon, Wed, Fri',
    class_timing: '10:00 AM - 12:00 PM',
    capacity: 30,
    status: 'upcoming',
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  const fetchBatches = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);

      const res = await api.get(`/api/batches?${params.toString()}`);
      setBatches(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, [page, statusFilter]);

  const handleOpenCreate = async () => {
    try {
      const [cRes, iRes] = await Promise.all([
        api.get('/api/courses?page=1&page_size=50'),
        api.get('/api/instructors?page=1&page_size=50'),
      ]);
      setCourses(cRes.data.items || []);
      setInstructors(iRes.data.items || []);
      setIsCreateOpen(true);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleCreateBatch = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      const res = await api.post('/api/batches', {
        ...createForm,
        course_id: parseInt(createForm.course_id),
        instructor_id: parseInt(createForm.instructor_id),
        capacity: parseInt(createForm.capacity) || 30,
      });
      toast.success('Batch created successfully!');
      setIsCreateOpen(false);
      navigate(`/batches/${res.data.id}`);
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const columns = [
    {
      header: 'Batch Code',
      key: 'batch_code',
      render: (code) => (
        <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
          {code}
        </span>
      ),
    },
    {
      header: 'Cohort Name',
      key: 'name',
      render: (_, row) => (
        <div>
          <Link to={`/batches/${row.id}`} className="font-bold text-slate-900 hover:text-brand-600">
            {row.name}
          </Link>
          <p className="text-xs text-slate-500">{row.course_name || `Course #${row.course_id}`}</p>
        </div>
      ),
    },
    {
      header: 'Instructor',
      key: 'instructor_name',
      render: (name) => <span className="text-xs font-medium text-slate-700">{name || '-'}</span>,
    },
    {
      header: 'Schedule',
      key: 'class_timing',
      render: (_, row) => (
        <div className="text-xs">
          <p className="font-semibold text-slate-800">{row.class_days}</p>
          <p className="text-slate-400">{row.class_timing}</p>
        </div>
      ),
    },
    {
      header: 'Capacity',
      key: 'capacity',
      render: (_, row) => {
        const pct = Math.round(((row.enrolled_count || 0) / (row.capacity || 1)) * 100);
        return (
          <div className="w-28 text-xs">
            <div className="flex justify-between font-semibold text-slate-700 mb-1">
              <span>{row.enrolled_count || 0}/{row.capacity}</span>
              <span>{pct}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-1.5 rounded-full ${pct >= 100 ? 'bg-rose-500' : 'bg-brand-600'}`}
                style={{ width: `${Math.min(100, pct)}%` }}
              />
            </div>
          </div>
        );
      },
    },
    {
      header: 'Status',
      key: 'status',
      render: (status) => <Badge status={status} />,
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) => (
        <Link to={`/batches/${row.id}`}>
          <Button size="sm" variant="secondary">
            View Roster
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Batches & Cohorts</h1>
          <p className="text-xs text-slate-500 mt-0.5">Manage class schedules, student rosters, and cohort capacities</p>
        </div>
        {role === ROLES.ADMIN && (
          <Button variant="primary" icon={HiOutlinePlus} onClick={handleOpenCreate}>
            Create New Batch
          </Button>
        )}
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            fetchBatches();
          }}
          className="flex gap-2 flex-1 max-w-md w-full"
        >
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by code or batch name..."
            icon={HiOutlineMagnifyingGlass}
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>

        <Select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          placeholder="All Batch Statuses"
          options={[
            { value: 'upcoming', label: 'Upcoming' },
            { value: 'active', label: 'Active' },
            { value: 'closed', label: 'Closed' },
            { value: 'archived', label: 'Archived' },
          ]}
          className="w-44"
        />
      </div>

      <DataTable
        columns={columns}
        data={batches}
        isLoading={loading}
        emptyMessage="No batches found"
        onRowClick={(row) => navigate(`/batches/${row.id}`)}
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Create Batch Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Schedule New Batch"
        subtitle="Configure schedule timing, instructor, and student capacity"
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreateBatch} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Batch Code"
              value={createForm.batch_code}
              onChange={(e) => setCreateForm({ ...createForm, batch_code: e.target.value })}
              placeholder="e.g. BATCH-2026-A"
              required
            />
            <div className="sm:col-span-2">
              <Input
                label="Batch Name"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                placeholder="e.g. Summer Morning Cohort"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Target Course *
              </label>
              <select
                value={createForm.course_id}
                onChange={(e) => setCreateForm({ ...createForm, course_id: e.target.value })}
                className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
                required
              >
                <option value="">Select course...</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.course_code} - {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Lead Instructor *
              </label>
              <select
                value={createForm.instructor_id}
                onChange={(e) => setCreateForm({ ...createForm, instructor_id: e.target.value })}
                className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
                required
              >
                <option value="">Select instructor...</option>
                {instructors.map((inst) => (
                  <option key={inst.instructor_profile_id} value={inst.instructor_profile_id}>
                    {inst.full_name} ({inst.employee_code})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Start Date"
              type="date"
              value={createForm.start_date}
              onChange={(e) => setCreateForm({ ...createForm, start_date: e.target.value })}
              required
            />
            <Input
              label="End Date"
              type="date"
              value={createForm.end_date}
              onChange={(e) => setCreateForm({ ...createForm, end_date: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Class Days"
              value={createForm.class_days}
              onChange={(e) => setCreateForm({ ...createForm, class_days: e.target.value })}
              placeholder="e.g. Mon, Wed, Fri"
              required
            />
            <Input
              label="Class Timing"
              value={createForm.class_timing}
              onChange={(e) => setCreateForm({ ...createForm, class_timing: e.target.value })}
              placeholder="e.g. 10:00 AM - 12:00 PM"
              required
            />
            <Input
              label="Seat Capacity"
              type="number"
              min="1"
              max="1000"
              value={createForm.capacity}
              onChange={(e) => setCreateForm({ ...createForm, capacity: e.target.value })}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Schedule Batch
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
