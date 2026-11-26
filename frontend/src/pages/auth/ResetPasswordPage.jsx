import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { HiOutlineKey, HiOutlineLockClosed, HiOutlineArrowLeft } from 'react-icons/hi';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [formData, setFormData] = useState({
    token: searchParams.get('token') || '',
    new_password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.token || !formData.new_password) {
      setError('Please fill in both reset token and new password.');
      return;
    }
    if (formData.new_password !== formData.confirm_password) {
      setError('New passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.post('/api/auth/reset-password', {
        token: formData.token,
        new_password: formData.new_password,
      });
      toast.success(res.data.message || 'Password reset successfully! Please sign in.');
      navigate('/login');
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6 text-center">
        <h3 className="text-lg font-bold text-slate-900">Set new password</h3>
        <p className="text-xs text-slate-500 mt-1">Enter your reset token and your new secure password</p>
      </div>

      <ErrorAlert message={error} onClose={() => setError('')} />

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Reset Token"
          type="text"
          name="token"
          value={formData.token}
          onChange={handleChange}
          placeholder="Paste reset token here"
          icon={HiOutlineKey}
          required
        />

        <Input
          label="New Password"
          type="password"
          name="new_password"
          value={formData.new_password}
          onChange={handleChange}
          placeholder="Min 8 characters"
          icon={HiOutlineLockClosed}
          required
        />

        <Input
          label="Confirm New Password"
          type="password"
          name="confirm_password"
          value={formData.confirm_password}
          onChange={handleChange}
          placeholder="Re-enter new password"
          icon={HiOutlineLockClosed}
          required
        />

        <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
          Reset Password
        </Button>

        <div className="text-center pt-3">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-brand-600 transition-colors"
          >
            <HiOutlineArrowLeft /> Back to Sign In
          </Link>
        </div>
      </form>
    </div>
  );
}
