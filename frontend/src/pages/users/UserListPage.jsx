import React, { useState, useEffect } from 'react';
import { HiOutlineUserPlus, HiOutlineMagnifyingGlass, HiOutlineKey, HiOutlineTrash, HiOutlinePencilSquare } from 'react-icons/hi2';
import DataTable from '../../components/tables/DataTable';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Select from '../../components/common/Select';
import Modal from '../../components/common/Modal';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import Badge from '../../components/common/Badge';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDate } from '../../utils/formatters';

export default function UserListPage() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'student',
    phone: '',
    is_active: true,
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  const [editUser, setEditUser] = useState(null);
  const [editForm, setEditForm] = useState({
    full_name: '',
    email: '',
    role: 'student',
    phone: '',
    is_active: true,
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState('');

  const [passwordResetUser, setPasswordResetUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  const [deleteUserTarget, setDeleteUserTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '15',
      });
      if (search) params.append('search', search);
      if (roleFilter) params.append('role', roleFilter);
      if (activeFilter !== '') params.append('is_active', activeFilter);

      const res = await api.get(`/api/users?${params.toString()}`);
      setUsers(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, roleFilter, activeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      await api.post('/api/users', createForm);
      toast.success('User account created successfully!');
      setIsCreateOpen(false);
      setCreateForm({
        full_name: '',
        email: '',
        password: '',
        role: 'student',
        phone: '',
        is_active: true,
      });
      fetchUsers();
    } catch (err) {
      setCreateError(getApiErrorMessage(err));
    } finally {
      setCreateLoading(false);
    }
  };

  const handleEditOpen = (user) => {
    setEditUser(user);
    setEditForm({
      full_name: user.full_name,
      email: user.email,
      role: user.role,
      phone: user.phone || '',
      is_active: user.is_active,
    });
    setEditError('');
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setEditLoading(true);
    setEditError('');
    try {
      await api.put(`/api/users/${editUser.id}`, editForm);
      toast.success('User updated successfully!');
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      setEditError(getApiErrorMessage(err));
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteUserTarget) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/api/users/${deleteUserTarget.id}`);
      toast.success('User deactivated successfully!');
      setDeleteUserTarget(null);
      fetchUsers();
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleAdminResetPassword = async (e) => {
    e.preventDefault();
    if (!newPassword || newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long.');
      return;
    }
    setResetLoading(true);
    try {
      await api.post(`/api/users/${passwordResetUser.id}/reset-password`, {
        new_password: newPassword,
      });
      toast.success(`Password override applied for ${passwordResetUser.full_name}`);
      setPasswordResetUser(null);
      setNewPassword('');
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setResetLoading(false);
    }
  };

  const columns = [
    {
      header: 'User',
      key: 'full_name',
      render: (_, row) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
            {row.full_name ? row.full_name[0].toUpperCase() : 'U'}
          </div>
          <div>
            <p className="font-semibold text-slate-900 leading-tight">{row.full_name}</p>
            <p className="text-xs text-slate-500">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      header: 'Role',
      key: 'role',
      render: (role) => <Badge status={role} />,
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
      header: 'Phone',
      key: 'phone',
      render: (phone) => phone || '-',
    },
    {
      header: 'Joined Date',
      key: 'created_at',
      render: (date) => formatDate(date),
    },
    {
      header: 'Actions',
      key: 'actions',
      align: 'right',
      render: (_, row) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => handleEditOpen(row)}
            className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            title="Edit User"
          >
            <HiOutlinePencilSquare className="text-base" />
          </button>
          <button
            onClick={() => setPasswordResetUser(row)}
            className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer"
            title="Force Reset Password"
          >
            <HiOutlineKey className="text-base" />
          </button>
          <button
            onClick={() => setDeleteUserTarget(row)}
            className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
            title="Deactivate Account"
          >
            <HiOutlineTrash className="text-base" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">User Directory</h1>
          <p className="text-xs text-slate-500 mt-0.5">Manage system access, roles, and administrative accounts</p>
        </div>
        <Button
          variant="primary"
          icon={HiOutlineUserPlus}
          onClick={() => setIsCreateOpen(true)}
        >
          Add New User
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full md:max-w-md flex gap-2">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or email..."
            icon={HiOutlineMagnifyingGlass}
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
            placeholder="All Roles"
            options={[
              { value: 'admin', label: 'Admin' },
              { value: 'instructor', label: 'Instructor' },
              { value: 'student', label: 'Student' },
            ]}
            className="w-36"
          />
          <Select
            value={activeFilter}
            onChange={(e) => {
              setActiveFilter(e.target.value);
              setPage(1);
            }}
            placeholder="All Status"
            options={[
              { value: 'true', label: 'Active' },
              { value: 'false', label: 'Inactive' },
            ]}
            className="w-36"
          />
        </div>
      </div>

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={users}
        isLoading={loading}
        emptyMessage="No users found"
        pagination={{
          currentPage: page,
          totalPages,
          totalItems: total,
          pageSize: 15,
          onPageChange: setPage,
        }}
      />

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create User Account"
        subtitle="Provision a new user account with role permissions"
      >
        <ErrorAlert message={createError} onClose={() => setCreateError('')} />
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Full Name"
            value={createForm.full_name}
            onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
            placeholder="e.g. Jane Smith"
            required
          />
          <Input
            label="Email Address"
            type="email"
            value={createForm.email}
            onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
            placeholder="user@example.com"
            required
          />
          <Input
            label="Initial Password"
            type="password"
            value={createForm.password}
            onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
            placeholder="Min 8 characters"
            required
          />
          <Select
            label="System Role"
            value={createForm.role}
            onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
            options={[
              { value: 'student', label: 'Student' },
              { value: 'instructor', label: 'Instructor' },
              { value: 'admin', label: 'Administrator' },
            ]}
            required
          />
          <Input
            label="Phone Number"
            value={createForm.phone}
            onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
            placeholder="+1 234 567 890"
          />
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Create User
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editUser}
        onClose={() => setEditUser(null)}
        title="Edit User Details"
        subtitle={`Updating ${editUser?.full_name}`}
      >
        <ErrorAlert message={editError} onClose={() => setEditError('')} />
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <Input
            label="Full Name"
            value={editForm.full_name}
            onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
            required
          />
          <Input
            label="Email Address"
            type="email"
            value={editForm.email}
            onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
            required
          />
          <Select
            label="System Role"
            value={editForm.role}
            onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
            options={[
              { value: 'student', label: 'Student' },
              { value: 'instructor', label: 'Instructor' },
              { value: 'admin', label: 'Administrator' },
            ]}
            required
          />
          <Input
            label="Phone Number"
            value={editForm.phone}
            onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
          />
          <Select
            label="Status"
            value={String(editForm.is_active)}
            onChange={(e) => setEditForm({ ...editForm, is_active: e.target.value === 'true' })}
            options={[
              { value: 'true', label: 'Active' },
              { value: 'false', label: 'Inactive / Suspended' },
            ]}
          />
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setEditUser(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={editLoading}>
              Save Updates
            </Button>
          </div>
        </form>
      </Modal>

      {/* Admin Reset Password Modal */}
      <Modal
        isOpen={!!passwordResetUser}
        onClose={() => setPasswordResetUser(null)}
        title="Admin Password Override"
        subtitle={`Set a new password for ${passwordResetUser?.full_name}`}
      >
        <form onSubmit={handleAdminResetPassword} className="space-y-4">
          <Input
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Enter min 8 characters password"
            required
          />
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="secondary" onClick={() => setPasswordResetUser(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={resetLoading}>
              Override Password
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete / Deactivate Confirm */}
      <ConfirmDialog
        isOpen={!!deleteUserTarget}
        onClose={() => setDeleteUserTarget(null)}
        onConfirm={handleDelete}
        title="Deactivate User Account?"
        message={`Are you sure you want to deactivate ${deleteUserTarget?.full_name}? The user will no longer be able to log in.`}
        confirmText="Deactivate"
        isLoading={deleteLoading}
      />
    </div>
  );
}
