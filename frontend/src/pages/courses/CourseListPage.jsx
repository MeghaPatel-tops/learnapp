import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import {
  HiOutlineAcademicCap,
  HiOutlinePlus,
  HiOutlineMagnifyingGlass,
  HiOutlineClock,
  HiOutlineCurrencyDollar,
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
import { formatCurrency, formatDate } from '../../utils/formatters';
import { ROLES } from '../../utils/constants';

export default function CourseListPage() {
  const navigate = useNavigate();
  const { role } = useSelector((state) => state.auth);

  const [courses, setCourses] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Create Course Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    course_code: '',
    name: '',
    description: '',
    category: 'Computer Science',
    duration_hours: 40,
    fee: '500.00',
    status: 'draft',
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);

      const res = await api.get(`/api/courses?${params.toString()}`);
      setCourses(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCourses();
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      const res = await api.post('/api/courses', {
        ...createForm,
        duration_hours: parseInt(createForm.duration_hours) || 1,
        fee: String(createForm.fee),
      });
      toast.success('Course created successfully!');
      setIsCreateOpen(false);
      navigate(`/courses/${res.data.id}`);
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const columns = [
    {
      header: 'Code',
      key: 'course_code',
      render: (code) => (
        <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
          {code}
        </span>
      ),
    },
    {
      header: 'Course Title',
      key: 'name',
      render: (_, row) => (
        <div>
          <Link
            to={`/courses/${row.id}`}
            className="font-bold text-slate-900 hover:text-brand-600 transition-colors"
          >
            {row.name}
          </Link>
          <p className="text-xs text-slate-500 line-clamp-1 mt-0.5">{row.description}</p>
        </div>
      ),
    },
    {
      header: 'Category',
      key: 'category',
      render: (cat) => <span className="text-xs font-medium text-slate-600">{cat}</span>,
    },
    {
      header: 'Duration',
      key: 'duration_hours',
      render: (hours) => (
        <span className="inline-flex items-center gap-1 text-xs text-slate-600">
          <HiOutlineClock className="text-slate-400" />
          {hours} hrs
        </span>
      ),
    },
    {
      header: 'Fee',
      key: 'fee',
      render: (fee) => (
        <span className="font-semibold text-slate-800 text-xs">
          {formatCurrency(fee)}
        </span>
      ),
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
        <Link to={`/courses/${row.id}`}>
          <Button size="sm" variant="secondary">
            View Syllabus
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Courses & Curriculum</h1>
          <p className="text-xs text-slate-500 mt-0.5">Explore syllabus, modules, video lectures, and study materials</p>
        </div>
        {role === ROLES.ADMIN && (
          <Button variant="primary" icon={HiOutlinePlus} onClick={() => setIsCreateOpen(true)}>
            Create New Course
          </Button>
        )}
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 flex-1 max-w-md w-full">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by course code or title..."
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
          placeholder="All Course Statuses"
          options={[
            { value: 'published', label: 'Published' },
            { value: 'draft', label: 'Draft' },
            { value: 'archived', label: 'Archived' },
          ]}
          className="w-44"
        />
      </div>

      <DataTable
        columns={columns}
        data={courses}
        isLoading={loading}
        emptyMessage="No courses found"
        onRowClick={(row) => navigate(`/courses/${row.id}`)}
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Create Course Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Course"
        subtitle="Define course metadata and curriculum configuration"
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Course Code"
              value={createForm.course_code}
              onChange={(e) => setCreateForm({ ...createForm, course_code: e.target.value })}
              placeholder="e.g. CS-101"
              required
            />
            <div className="sm:col-span-2">
              <Input
                label="Course Title"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                placeholder="e.g. Modern Full-Stack Web Development"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Course Description *
            </label>
            <textarea
              rows={3}
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Comprehensive course syllabus overview..."
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Category"
              value={createForm.category}
              onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
              placeholder="e.g. Web Development"
              required
            />
            <Input
              label="Duration (Hours)"
              type="number"
              min="1"
              value={createForm.duration_hours}
              onChange={(e) => setCreateForm({ ...createForm, duration_hours: e.target.value })}
              required
            />
            <Input
              label="Tuition Fee ($)"
              type="number"
              step="0.01"
              min="0"
              value={createForm.fee}
              onChange={(e) => setCreateForm({ ...createForm, fee: e.target.value })}
              required
            />
          </div>

          <Select
            label="Initial Status"
            value={createForm.status}
            onChange={(e) => setCreateForm({ ...createForm, status: e.target.value })}
            options={[
              { value: 'draft', label: 'Draft' },
              { value: 'published', label: 'Published' },
            ]}
          />

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Create Course
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
