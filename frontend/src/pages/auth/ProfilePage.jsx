import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import Card from '../../components/common/Card';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import { updateCurrentUser } from '../../store/authSlice';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import { formatDateTime } from '../../utils/formatters';

export default function ProfilePage() {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);

  const [profileForm, setProfileForm] = useState({
    full_name: '',
    phone: '',
    avatar_url: '',
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState('');

  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  useEffect(() => {
    if (user) {
      setProfileForm({
        full_name: user.full_name || '',
        phone: user.phone || '',
        avatar_url: user.avatar_url || '',
      });
    }
  }, [user]);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileError('');
    try {
      const res = await api.put('/api/auth/me', profileForm);
      dispatch(updateCurrentUser(res.data));
      toast.success('Profile updated successfully!');
    } catch (err) {
      setProfileError(getApiErrorMessage(err));
    } finally {
      setProfileLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('New password and confirmation do not match.');
      return;
    }
    setPasswordLoading(true);
    setPasswordError('');
    try {
      await api.post('/api/auth/change-password', {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      toast.success('Password changed successfully!');
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (err) {
      setPasswordError(getApiErrorMessage(err));
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Account Settings</h1>
        <p className="text-xs text-slate-500 mt-0.5">Manage your personal profile and account credentials</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* User Card */}
        <Card className="md:col-span-1 h-fit text-center">
          <div className="w-20 h-20 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-2xl mx-auto mb-4 ring-4 ring-brand-100 shadow-md">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <h3 className="font-bold text-slate-900 text-base">{user?.full_name}</h3>
          <p className="text-xs text-slate-500">{user?.email}</p>
          <div className="mt-3">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-600/20">
              {user?.role}
            </span>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 text-left text-xs text-slate-500 space-y-2">
            <div className="flex justify-between">
              <span>Account Status:</span>
              <span className="font-semibold text-emerald-600">Active</span>
            </div>
            <div className="flex justify-between">
              <span>Last Login:</span>
              <span className="font-medium text-slate-700">{formatDateTime(user?.last_login_at)}</span>
            </div>
            <div className="flex justify-between">
              <span>Member Since:</span>
              <span className="font-medium text-slate-700">{formatDateTime(user?.created_at)}</span>
            </div>
          </div>
        </Card>

        {/* Profile & Password Tabs/Cards */}
        <div className="md:col-span-2 space-y-6">
          <Card title="Personal Information" subtitle="Update your basic display information">
            <ErrorAlert message={profileError} onClose={() => setProfileError('')} />
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <Input
                label="Full Name"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                required
              />
              <Input
                label="Email Address"
                value={user?.email || ''}
                disabled
                helperText="Email cannot be changed directly"
              />
              <Input
                label="Phone Number"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                placeholder="+1 (555) 000-0000"
              />
              <div className="flex justify-end pt-2">
                <Button type="submit" variant="primary" isLoading={profileLoading}>
                  Save Changes
                </Button>
              </div>
            </form>
          </Card>

          <Card title="Security & Password" subtitle="Change your password regularly for better security">
            <ErrorAlert message={passwordError} onClose={() => setPasswordError('')} />
            <form onSubmit={handleChangePassword} className="space-y-4">
              <Input
                label="Current Password"
                type="password"
                value={passwordForm.current_password}
                onChange={(e) =>
                  setPasswordForm({ ...passwordForm, current_password: e.target.value })
                }
                required
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="New Password"
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) =>
                    setPasswordForm({ ...passwordForm, new_password: e.target.value })
                  }
                  required
                />
                <Input
                  label="Confirm New Password"
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) =>
                    setPasswordForm({ ...passwordForm, confirm_password: e.target.value })
                  }
                  required
                />
              </div>
              <div className="flex justify-end pt-2">
                <Button type="submit" variant="secondary" isLoading={passwordLoading}>
                  Update Password
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
