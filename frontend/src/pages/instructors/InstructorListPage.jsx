import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
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
import { ROLES } from '../../utils/constants';

export default function InstructorListPage() {
  const { role } = useSelector((state) => state.auth);
  const [instructors, setInstructors] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Detail Modal
  const [selectedInstructor, setSelectedInstructor] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    full_name: '',
    email: '',
    password: '',
    phone: '',
    employee_code: '',
    expertise: '',
    qualification: '',
    bio: '',
    experience_years: 0,
    is_active: true,
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  const fetchInstructors = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (search) params.append('search', search);

      const res = await api.get(`/api/instructors?${params.toString()}`);
      setInstructors(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstructors();
  }, [page]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchInstructors();
  };

  const handleViewDetail = async (inst) => {
    setDetailLoading(true);
    try {
      const res = await api.get(`/api/instructors/${inst.user_id}`);
      setSelectedInstructor(res.data);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      await api.post('/api/instructors', {
        ...createForm,
        experience_years: parseInt(createForm.experience_years) || 0,
      });
      toast.success('Instructor registered successfully!');
      setIsCreateOpen(false);
      setCreateForm({
        full_name: '',
        email: '',
        password: '',
        phone: '',
        employee_code: '',
        expertise: '',
        qualification: '',
        bio: '',
        experience_years: 0,
        is_active: true,
      });
      fetchInstructors();
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const columns = [
    {
      header: 'Code',
      key: 'employee_code',
      render: (code) => (
        <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
          {code}
        </span>
      ),
    },
    {
      header: 'Instructor Name',
      key: 'full_name',
      render: (_, row) => (
        <div>
          <p className="font-semibold text-slate-900 leading-tight">{row.full_name}</p>
          <p className="text-xs text-slate-500">{row.email}</p>
        </div>
      ),
    },
    {
      header: 'Expertise & Domain',
      key: 'expertise',
      render: (exp) => (
        <span className="text-xs font-medium text-slate-700">{exp || '-'}</span>
      ),
    },
    {
      header: 'Experience',
      key: 'experience_years',
      render: (years) => `${years || 0} years`,
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
          View Profile
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Faculty & Instructors</h1>
          <p className="text-xs text-slate-500 mt-0.5">Teaching personnel, course leaders, and academic profiles</p>
        </div>
        {role === ROLES.ADMIN && (
          <Button variant="primary" icon={HiOutlineUserPlus} onClick={() => setIsCreateOpen(true)}>
            Add Instructor
          </Button>
        )}
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-md">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search instructor by name, expertise..."
            icon={HiOutlineMagnifyingGlass}
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
      </div>

      <DataTable
        columns={columns}
        data={instructors}
        isLoading={loading}
        emptyMessage="No instructors found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Instructor Detail Modal */}
      <Modal
        isOpen={!!selectedInstructor}
        onClose={() => setSelectedInstructor(null)}
        title="Instructor Faculty Profile"
        subtitle={selectedInstructor?.full_name}
        maxWidth="max-w-2xl"
      >
        {selectedInstructor && (
          <div className="space-y-5 text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
              <div>
                <span className="text-slate-400 font-medium">Employee Code</span>
                <p className="font-mono font-bold text-slate-900 text-sm">{selectedInstructor.employee_code}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Email Address</span>
                <p className="font-semibold text-slate-900">{selectedInstructor.email}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Phone</span>
                <p className="font-semibold text-slate-900">{selectedInstructor.phone || '-'}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Expertise</span>
                <p className="font-semibold text-slate-900">{selectedInstructor.expertise || '-'}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Qualification</span>
                <p className="font-semibold text-slate-900">{selectedInstructor.qualification || '-'}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Experience</span>
                <p className="font-semibold text-slate-900">{selectedInstructor.experience_years} Years</p>
              </div>
            </div>

            {selectedInstructor.bio && (
              <div>
                <span className="text-slate-400 font-medium">Professional Biography</span>
                <p className="font-normal text-slate-700 mt-1 leading-relaxed bg-white p-3 rounded-lg border border-slate-100">
                  {selectedInstructor.bio}
                </p>
              </div>
            )}

            {/* Assigned Courses */}
            <div>
              <h4 className="font-bold text-slate-800 text-sm mb-2">Assigned Courses & Batches</h4>
              {(!selectedInstructor.assigned_courses || selectedInstructor.assigned_courses.length === 0) ? (
                <p className="text-slate-400">No active course assignments recorded</p>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden">
                  {selectedInstructor.assigned_courses.map((c, i) => (
                    <div key={i} className="p-3 flex items-center justify-between bg-white">
                      <div>
                        <p className="font-semibold text-slate-900">{c.name || `Course #${c.course_id}`}</p>
                        <p className="text-[10px] text-slate-400">{c.category || 'Curriculum'}</p>
                      </div>
                      <Badge status={c.status || 'active'} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Add Instructor Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register New Instructor"
        subtitle="Create faculty account and teaching credentials"
        maxWidth="max-w-xl"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreate} className="space-y-4">
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
              label="Initial Password"
              type="password"
              value={createForm.password}
              onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
              required
            />
            <Input
              label="Phone Number"
              value={createForm.phone}
              onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Employee Code (Optional)"
              value={createForm.employee_code}
              onChange={(e) => setCreateForm({ ...createForm, employee_code: e.target.value })}
              placeholder="e.g. INS-2026-001"
            />
            <Input
              label="Years of Experience"
              type="number"
              min="0"
              max="70"
              value={createForm.experience_years}
              onChange={(e) => setCreateForm({ ...createForm, experience_years: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Primary Expertise"
              value={createForm.expertise}
              onChange={(e) => setCreateForm({ ...createForm, expertise: e.target.value })}
              placeholder="e.g. React & Node.js"
            />
            <Input
              label="Academic Qualification"
              value={createForm.qualification}
              onChange={(e) => setCreateForm({ ...createForm, qualification: e.target.value })}
              placeholder="e.g. M.S. Computer Science"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Professional Biography
            </label>
            <textarea
              rows={3}
              value={createForm.bio}
              onChange={(e) => setCreateForm({ ...createForm, bio: e.target.value })}
              className="w-full rounded-lg border border-slate-300 text-sm p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Brief overview of teaching background..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Register Instructor
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
