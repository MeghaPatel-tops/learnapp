import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { HiOutlineBookOpen, HiOutlinePlus, HiOutlineMagnifyingGlass, HiOutlinePencilSquare } from 'react-icons/hi2';
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

export default function EnrollmentListPage() {
  const { role } = useSelector((state) => state.auth);

  const [enrollments, setEnrollments] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Enroll Modal
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [enrollForm, setEnrollForm] = useState({ student_id: '', course_id: '' });
  const [enrollLoading, setEnrollLoading] = useState(false);
  const [enrollError, setEnrollError] = useState('');

  // Edit status modal
  const [editEnrollment, setEditEnrollment] = useState(null);
  const [newStatus, setNewStatus] = useState('active');
  const [statusUpdateLoading, setStatusUpdateLoading] = useState(false);

  const fetchEnrollments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (statusFilter) params.append('status', statusFilter);

      const res = await api.get(`/api/enrollments?${params.toString()}`);
      setEnrollments(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnrollments();
  }, [page, statusFilter]);

  const handleOpenEnrollModal = async () => {
    try {
      const [sRes, cRes] = await Promise.all([
        api.get('/api/students?page=1&page_size=100'),
        api.get('/api/courses?page=1&page_size=100'),
      ]);
      setStudents(sRes.data.items || []);
      setCourses(cRes.data.items || []);
      setIsEnrollModalOpen(true);
      setEnrollError('');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  const handleCreateEnrollment = async (e) => {
    e.preventDefault();
    if (!enrollForm.student_id || !enrollForm.course_id) return;

    setEnrollLoading(true);
    setEnrollError('');
    try {
      await api.post('/api/enrollments', {
        student_id: parseInt(enrollForm.student_id),
        course_id: parseInt(enrollForm.course_id),
      });
      toast.success('Student enrolled into course successfully!');
      setIsEnrollModalOpen(false);
      setEnrollForm({ student_id: '', course_id: '' });
      fetchEnrollments();
    } catch (err) {
      setEnrollError(getApiErrorMessage(err));
    } finally {
      setEnrollLoading(false);
    }
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    if (!editEnrollment) return;

    setStatusUpdateLoading(true);
    try {
      await api.put(`/api/enrollments/${editEnrollment.id}`, { status: newStatus });
      toast.success('Enrollment status updated');
      setEditEnrollment(null);
      fetchEnrollments();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setStatusUpdateLoading(false);
    }
  };

  const columns = [
    {
      header: 'ID',
      key: 'id',
      render: (id) => <span className="font-mono text-xs font-bold text-slate-500">#{id}</span>,
    },
    {
      header: 'Student',
      key: 'student_name',
      render: (name, row) => (
        <div>
          <p className="font-semibold text-slate-900">{name || `Student #${row.student_id}`}</p>
          <p className="text-xs text-slate-400">ID: {row.student_id}</p>
        </div>
      ),
    },
    {
      header: 'Enrolled Course',
      key: 'course_name',
      render: (name, row) => (
        <span className="font-medium text-slate-800 text-xs">
          {name || `Course #${row.course_id}`}
        </span>
      ),
    },
    {
      header: 'Enrollment Date',
      key: 'enrolled_at',
      render: (date) => formatDate(date),
    },
    {
      header: 'Status',
      key: 'status',
      render: (status) => <Badge status={status} />,
    },
    {
      header: 'Completion Date',
      key: 'completed_at',
      render: (date) => formatDate(date),
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) =>
        role === ROLES.ADMIN ? (
          <Button
            size="sm"
            variant="ghost"
            icon={HiOutlinePencilSquare}
            onClick={() => {
              setEditEnrollment(row);
              setNewStatus(row.status);
            }}
          >
            Update
          </Button>
        ) : null,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Course Enrollments</h1>
          <p className="text-xs text-slate-500 mt-0.5">Manage learner admissions, active statuses, and academic completions</p>
        </div>
        {role === ROLES.ADMIN && (
          <Button variant="primary" icon={HiOutlinePlus} onClick={handleOpenEnrollModal}>
            New Course Enrollment
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
          placeholder="All Enrollment Statuses"
          options={[
            { value: 'active', label: 'Active' },
            { value: 'completed', label: 'Completed' },
            { value: 'dropped', label: 'Dropped' },
          ]}
          className="w-48"
        />
      </div>

      <DataTable
        columns={columns}
        data={enrollments}
        isLoading={loading}
        emptyMessage="No enrollments found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Enroll Student Modal */}
      <Modal
        isOpen={isEnrollModalOpen}
        onClose={() => setIsEnrollModalOpen(false)}
        title="Enroll Student in Course"
        subtitle="Registers student for curriculum access (Enforces unique enrollment)"
      >
        <ErrorAlert message={enrollError} onClose={() => setEnrollError('')} />
        <form onSubmit={handleCreateEnrollment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Student *
            </label>
            <select
              value={enrollForm.student_id}
              onChange={(e) => setEnrollForm({ ...enrollForm, student_id: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              <option value="">Choose a student...</option>
              {students.map((st) => (
                <option key={st.user_id} value={st.user_id}>
                  {st.student_code} - {st.full_name} ({st.email})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Course *
            </label>
            <select
              value={enrollForm.course_id}
              onChange={(e) => setEnrollForm({ ...enrollForm, course_id: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              <option value="">Choose a course...</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.course_code} - {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsEnrollModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={enrollLoading}>
              Enroll Student
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Status Modal */}
      <Modal
        isOpen={!!editEnrollment}
        onClose={() => setEditEnrollment(null)}
        title="Update Enrollment Status"
        subtitle={`Student #${editEnrollment?.student_id} - ${editEnrollment?.course_name}`}
      >
        <form onSubmit={handleUpdateStatus} className="space-y-4">
          <Select
            label="Enrollment Status"
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            options={[
              { value: 'active', label: 'Active' },
              { value: 'completed', label: 'Completed' },
              { value: 'dropped', label: 'Dropped' },
            ]}
          />
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setEditEnrollment(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={statusUpdateLoading}>
              Save Status
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
