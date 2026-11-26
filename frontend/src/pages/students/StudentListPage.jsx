import React, { useState, useEffect } from 'react';
import { HiOutlineMagnifyingGlass, HiOutlineUserPlus, HiOutlineEye } from 'react-icons/hi2';
import DataTable from '../../components/tables/DataTable';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDate } from '../../utils/formatters';

export default function StudentListPage() {
  const [students, setStudents] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Detail Modal
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create Student Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    full_name: '',
    email: '',
    password: '',
    phone: '',
    student_code: '',
    date_of_birth: '',
    address: '',
    guardian_name: '',
    guardian_phone: '',
    is_active: true,
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (search) params.append('search', search);

      const res = await api.get(`/api/students?${params.toString()}`);
      setStudents(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [page]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchStudents();
  };

  const handleViewDetail = async (student) => {
    setDetailLoading(true);
    try {
      const res = await api.get(`/api/students/${student.user_id}`);
      setSelectedStudent(res.data);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateStudent = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      await api.post('/api/students', createForm);
      toast.success('Student registered successfully!');
      setIsCreateOpen(false);
      setCreateForm({
        full_name: '',
        email: '',
        password: '',
        phone: '',
        student_code: '',
        date_of_birth: '',
        address: '',
        guardian_name: '',
        guardian_phone: '',
        is_active: true,
      });
      fetchStudents();
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const columns = [
    {
      header: 'Code',
      key: 'student_code',
      render: (code) => (
        <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
          {code}
        </span>
      ),
    },
    {
      header: 'Student Name',
      key: 'full_name',
      render: (_, row) => (
        <div>
          <p className="font-semibold text-slate-900 leading-tight">{row.full_name}</p>
          <p className="text-xs text-slate-500">{row.email}</p>
        </div>
      ),
    },
    {
      header: 'Guardian',
      key: 'guardian_name',
      render: (guardian, row) =>
        guardian ? (
          <div>
            <p className="text-xs font-medium text-slate-800">{guardian}</p>
            <p className="text-[10px] text-slate-400">{row.guardian_phone || ''}</p>
          </div>
        ) : (
          '-'
        ),
    },
    {
      header: 'Status',
      key: 'is_active',
      render: (isActive) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
            isActive ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
          }`}
        >
          {isActive ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      header: 'Created',
      key: 'created_at',
      render: (date) => formatDate(date),
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) => (
        <Button
          size="sm"
          variant="secondary"
          icon={HiOutlineEye}
          onClick={() => handleViewDetail(row)}
        >
          Details
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Student Directory</h1>
          <p className="text-xs text-slate-500 mt-0.5">Academic records, guardian details, and course enrollments</p>
        </div>
        <Button variant="primary" icon={HiOutlineUserPlus} onClick={() => setIsCreateOpen(true)}>
          Register Student
        </Button>
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-md">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by code, name or email..."
            icon={HiOutlineMagnifyingGlass}
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
      </div>

      <DataTable
        columns={columns}
        data={students}
        isLoading={loading}
        emptyMessage="No students found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Student Details Modal */}
      <Modal
        isOpen={!!selectedStudent}
        onClose={() => setSelectedStudent(null)}
        title="Student Academic Profile"
        subtitle={selectedStudent?.full_name}
        maxWidth="max-w-2xl"
      >
        {selectedStudent && (
          <div className="space-y-5 text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
              <div>
                <span className="text-slate-400 font-medium">Student Code</span>
                <p className="font-mono font-bold text-slate-900 text-sm">{selectedStudent.student_code}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Email Address</span>
                <p className="font-semibold text-slate-900">{selectedStudent.email}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Phone</span>
                <p className="font-semibold text-slate-900">{selectedStudent.phone || '-'}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Date of Birth</span>
                <p className="font-semibold text-slate-900">{formatDate(selectedStudent.date_of_birth)}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Guardian</span>
                <p className="font-semibold text-slate-900">{selectedStudent.guardian_name || '-'}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Guardian Phone</span>
                <p className="font-semibold text-slate-900">{selectedStudent.guardian_phone || '-'}</p>
              </div>
            </div>

            {selectedStudent.address && (
              <div>
                <span className="text-slate-400 font-medium">Residential Address</span>
                <p className="font-medium text-slate-700 mt-0.5">{selectedStudent.address}</p>
              </div>
            )}

            {/* Enrolled Courses */}
            <div>
              <h4 className="font-bold text-slate-800 text-sm mb-2">Enrolled Courses</h4>
              {!selectedStudent.enrollments || selectedStudent.enrollments.length === 0 ? (
                <p className="text-slate-400">No active course enrollments</p>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden">
                  {selectedStudent.enrollments.map((enr, i) => (
                    <div key={i} className="p-3 flex items-center justify-between bg-white">
                      <div>
                        <p className="font-semibold text-slate-900">{enr.course_name || `Course #${enr.course_id}`}</p>
                        <p className="text-[10px] text-slate-400">Enrolled: {formatDate(enr.enrolled_at)}</p>
                      </div>
                      <Badge status={enr.status} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Register Student Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register New Student"
        subtitle="Create user login and student academic profile"
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreateStudent} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={createForm.full_name}
              onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
              required
            />
            <Input
              label="Email Address"
              type="email"
              value={createForm.email}
              onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
              required
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Password"
              type="password"
              value={createForm.password}
              onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
              required
            />
            <Input
              label="Phone"
              value={createForm.phone}
              onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Student Code (Optional)"
              value={createForm.student_code}
              onChange={(e) => setCreateForm({ ...createForm, student_code: e.target.value })}
              placeholder="Auto-generated if empty"
            />
            <Input
              label="Date of Birth"
              type="date"
              value={createForm.date_of_birth}
              onChange={(e) => setCreateForm({ ...createForm, date_of_birth: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Guardian Name"
              value={createForm.guardian_name}
              onChange={(e) => setCreateForm({ ...createForm, guardian_name: e.target.value })}
            />
            <Input
              label="Guardian Phone"
              value={createForm.guardian_phone}
              onChange={(e) => setCreateForm({ ...createForm, guardian_phone: e.target.value })}
            />
          </div>
          <Input
            label="Address"
            value={createForm.address}
            onChange={(e) => setCreateForm({ ...createForm, address: e.target.value })}
          />

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Register Student
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
