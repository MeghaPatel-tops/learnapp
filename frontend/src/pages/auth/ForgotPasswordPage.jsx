import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { HiOutlineMail, HiOutlineArrowLeft } from 'react-icons/hi';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import ErrorAlert from '../../components/feedback/ErrorAlert';
import api, { getApiErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      setError('Please provide your registered email address.');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const res = await api.post('/api/auth/forgot-password', { email });
      setIsSuccess(true);
      toast.success(res.data.message || 'Password reset instructions sent');
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6 text-center">
        <h3 className="text-lg font-bold text-slate-900">Reset your password</h3>
        <p className="text-xs text-slate-500 mt-1">
          Enter your email address and we'll send you instructions to reset your password.
        </p>
      </div>

      <ErrorAlert message={error} onClose={() => setError('')} />

      {isSuccess ? (
        <div className="text-center py-4 space-y-4">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto text-xl font-bold">
            ✓
          </div>
          <p className="text-xs text-slate-600">
            If an account with that email exists, password reset instructions have been dispatched. Check your inbox or proceed to the reset page.
          </p>
          <div className="flex flex-col gap-2 pt-2">
            <Link to="/reset-password">
              <Button variant="outline" className="w-full text-xs">
                Enter Reset Token
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="ghost" className="w-full text-xs" icon={HiOutlineArrowLeft}>
                Back to Sign In
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your-email@example.com"
            icon={HiOutlineMail}
            required
          />

          <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
            Send Reset Link
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
      )}
    </div>
  );
}
